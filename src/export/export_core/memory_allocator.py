from collections import defaultdict, deque
import math

class MemoryAllocator:
    def __init__(self, graph, value_info, element_size_bytes=1, verbose=False):
        self.graph = graph
        self.value_info = value_info
        self.element_size = element_size_bytes
        self.verbose = verbose

        # ONNX initializers — considered ROM
        self.initializer_names = {init.name for init in graph.initializer}
        self.model_inputs = {vi.name for vi in graph.input}
        self.model_outputs = {vi.name for vi in graph.output}

        # computed
        self.tensor_sizes = {}    # in bytes
        self.tensor_offsets = {}
        self.total_buffer_size = 0

        # helpers
        self._producer_map_cache = None  # filled on demand: tensor_name -> producer_node_index

    # -------------------- producer map --------------------
    def _build_producer_map(self):
        """Map tensor name -> (producer_node_index, producer_node)."""
        if self._producer_map_cache is not None:
            return self._producer_map_cache
        m = {}
        for idx, node in enumerate(self.graph.node):
            for out in node.output:
                if out:
                    m[out] = (idx, node)
        self._producer_map_cache = m
        return m

    # -------------------- size calculation with DequantizeLinear skip --------------------
    def calculate_tensor_sizes(self):
        """
        Calculate size (in bytes) for each tensor that we should track in RAM.
        Skip:
          - explicit graph.initializer names
          - outputs of DequantizeLinear whose input[0] is an initializer (quantized weights -> dequantized weights in ROM)
          - tensors that are not produced by any node and not a model input (likely constants/weights)
          - optionally skip weight/bias names that slip through (heuristic)
        """
        produced_map = self._build_producer_map()
        self.tensor_sizes = {}

        skipped = []
        included = []

        for name, vi in self.value_info.items():
            if not name:
                continue

            # 1) explicit initializers -> ROM
            if name in self.initializer_names:
                skipped.append((name, "explicit-initializer"))
                continue

            # 2) if produced by DequantizeLinear whose input[0] is an initializer -> skip (treat as ROM)
            prod = produced_map.get(name, None)
            if prod is not None:
                prod_idx, prod_node = prod
                if getattr(prod_node, "op_type", "").lower() == "dequantizelinear":
                    # check the first input: if it's an initializer then this DequantizeLinear is dequantizing a ROM constant
                    if prod_node.input and len(prod_node.input) >= 1:
                        qin = prod_node.input[0]
                        if qin in self.initializer_names:
                            skipped.append((name, "dequantize_of_initializer -> skip (ROM)"))
                            continue

            # 3) if not produced by any node and not a model input/output -> likely a constant (skip)
            if (name not in produced_map) and (name not in self.model_inputs) and (name not in self.model_outputs):
                skipped.append((name, "not-produced and not model-input/output -> likely constant"))
                continue

            # 4) heuristic skip by name (weights/bias) if not produced and not model input
            lname = name.lower()
            if ("weight" in lname or "weights" in lname or "bias" in lname) and (name not in self.model_inputs):
                # allow weights that are produced by nodes (rare), but skip otherwise
                if name not in produced_map:
                    skipped.append((name, "heuristic-skip weight/bias"))
                    continue

            # 5) compute element count (must have concrete dims)
            try:
                shape = vi.type.tensor_type.shape
            except Exception:
                skipped.append((name, "no-shape"))
                continue

            elem_count = 1
            unknown = False
            for dim in shape.dim:
                if dim.HasField('dim_value'):
                    elem_count *= dim.dim_value
                else:
                    unknown = True
                    break
            if unknown:
                skipped.append((name, "symbolic-dim"))
                continue

            byte_size = int(elem_count) * int(self.element_size)
            self.tensor_sizes[name] = byte_size
            included.append((name, byte_size))

        if self.verbose:
            print("=== calculate_tensor_sizes summary ===")
            print(f"Initializers (ROM): {len(self.initializer_names)}")
            print(f"Produced tensors by nodes: {len(produced_map)}")
            print(f"Included tensors (RAM tracked): {len(included)}")
            for n, s in included:
                print(f"  + {n}: {s} bytes")
            print(f"Skipped: {len(skipped)}")
            for n, reason in skipped:
                print(f"  - {n}: {reason}")
            print("======================================")

    def _is_activation_input(self, node, input_name, input_index):
        """
        Return True if this input should be treated as a RAM activation.
        We ignore:
          - explicit initializers
          - qgemmcustom inputs 1..6 (quant params)
        """
        if not input_name:
            return False
        if input_name in self.initializer_names:
            return False

        if node.op_type and node.op_type.lower() == "qgemmcustom":
            if 1 <= input_index <= 6:
                return False

        return True

    def _topo_sort_nodes(self):
        tensor_producer = {}
        for idx, node in enumerate(self.graph.node):
            for out_name in node.output:
                if out_name:
                    tensor_producer[out_name] = idx

        adj = defaultdict(list)
        indeg = [0] * len(self.graph.node)

        for idx, node in enumerate(self.graph.node):
            for in_name in node.input:
                if not in_name:
                    continue
                prod = tensor_producer.get(in_name, None)
                if prod is not None and prod != idx:
                    adj[prod].append(idx)
                    indeg[idx] += 1

        q = deque([i for i in range(len(self.graph.node)) if indeg[i] == 0])
        order = []
        seen = set(q)
        while q:
            u = q.popleft()
            order.append(u)
            for v in adj.get(u, []):
                indeg[v] -= 1
                if indeg[v] == 0 and v not in seen:
                    q.append(v)
                    seen.add(v)

        if len(order) < len(self.graph.node):
            for i in range(len(self.graph.node)):
                if i not in order:
                    order.append(i)
        return order

    def _coalesce_free_list(self, free_list):
        if not free_list:
            return free_list
        free_list.sort()
        merged = []
        cur_off, cur_sz = free_list[0]
        for off, sz in free_list[1:]:
            if off == cur_off + cur_sz:
                cur_sz += sz
            else:
                merged.append((cur_off, cur_sz))
                cur_off, cur_sz = off, sz
        merged.append((cur_off, cur_sz))
        return merged

    def _alloc_block(self, free_list, size, current_buf_size):
        # best-fit
        best_idx = -1
        best_gap = None
        for i, (off, sz) in enumerate(free_list):
            if sz >= size:
                gap = sz - size
                if best_gap is None or gap < best_gap:
                    best_gap = gap
                    best_idx = i
        if best_idx >= 0:
            off, sz = free_list[best_idx]
            alloc_off = off
            if sz == size:
                del free_list[best_idx]
            else:
                free_list[best_idx] = (off + size, sz - size)
            return alloc_off, free_list, current_buf_size
        # extend
        alloc_off = current_buf_size
        current_buf_size += size
        return alloc_off, free_list, current_buf_size

    def allocate_with_reuse(self):
        if not self.tensor_sizes:
            raise RuntimeError("tensor_sizes empty — call calculate_tensor_sizes() first")

        order = self._topo_sort_nodes()
        N = len(order)

        # compute producers & consumers on topo indices
        producers = {}                 # tensor -> birth (node order idx)
        consumers = defaultdict(list)  # tensor -> list of consumer node order idx

        # model inputs born at -1
        for name in self.model_inputs:
            if name in self.tensor_sizes:
                producers[name] = -1

        # walk nodes in topo order
        for ord_idx, node_idx in enumerate(order):
            node = self.graph.node[node_idx]
            # consumers
            for in_idx, in_name in enumerate(node.input):
                if not in_name:
                    continue
                if in_name in self.tensor_sizes and self._is_activation_input(node, in_name, in_idx):
                    consumers[in_name].append(ord_idx)
            # producers
            for out_name in node.output:
                if not out_name:
                    continue
                if out_name in self.tensor_sizes:
                    producers[out_name] = ord_idx

        # build births/deaths
        births_by_node = defaultdict(list)
        deaths_by_node = defaultdict(list)

        for t_name, t_size in self.tensor_sizes.items():
            birth = producers.get(t_name, None)
            if birth is None:
                if self.verbose:
                    print(f"[WARN] tensor {t_name} has no producer and is not model input. Skipping.")
                continue

            if consumers[t_name]:
                death = max(consumers[t_name])
            else:
                if t_name in self.model_outputs:
                    death = N - 1
                else:
                    death = birth

            if t_name in self.model_outputs:
                death = max(death, N - 1)

            births_by_node[birth].append(t_name)
            deaths_by_node[death].append(t_name)

        # linear scan
        self.tensor_offsets = {}
        free_list = []
        buf_size = 0

        # allocate model-input births (-1)
        for t_name in births_by_node.get(-1, []):
            size = self.tensor_sizes[t_name]
            off, free_list, buf_size = self._alloc_block(free_list, size, buf_size)
            self.tensor_offsets[t_name] = off

        # node timeline
        for i in range(N):
            # allocate births at node i
            for t_name in births_by_node.get(i, []):
                size = self.tensor_sizes[t_name]
                off, free_list, buf_size = self._alloc_block(free_list, size, buf_size)
                self.tensor_offsets[t_name] = off

            # free deaths at node i (after node’s use)
            reclaimed = []
            for t_name in deaths_by_node.get(i, []):
                if t_name in self.tensor_offsets:
                    reclaimed.append((self.tensor_offsets[t_name], self.tensor_sizes[t_name]))
            if reclaimed:
                free_list.extend(reclaimed)
                free_list = self._coalesce_free_list(free_list)

        self.total_buffer_size = buf_size

        if self.verbose:
            print("=== allocate_with_reuse summary ===")
            print(f"Tracked tensors: {len(self.tensor_offsets)}")
            for name, off in sorted(self.tensor_offsets.items(), key=lambda x: x[1]):
                print(f"  {name}: offset={off}, size={self.tensor_sizes[name]}")
            print(f"Total buffer size (bytes): {self.total_buffer_size}")
            print("===================================")
