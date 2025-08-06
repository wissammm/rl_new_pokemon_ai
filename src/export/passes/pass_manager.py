class PassManager:
    def __init__(self, graph):
        self.graph = graph
        self.passes = []
        
    def add_pass(self, optimization_pass):
        self.passes.append(optimization_pass)
        
    def run_passes(self):
        """Run all registered passes in order"""
        for p in self.passes:
            p.run(self.graph)
        
    def get_optimized_graph(self):
        return self.graph