import re
import pydot
import itertools
import numpy as np
import networkx as nx

class Graph:
    def __init__(self, count=0, origin=""):
        """
        初始化一个空的邻接表图
        """
        self.adj_list = {}  # 邻接表，key: 节点ID, value: (label, [依赖的目标节点列表])
        self.node_count = count
        self.orignate = origin

    def get_edges(self):
        """
        获取图的所有边
        """
        return itertools.chain.from_iterable(
            ((from_id, to_id) for to_id in to_ids) for from_id, (_, to_ids) in self.adj_list.items()
        )


    def add_node(self, id, label):
        """
        添加一个新节点
        :param id: 节点的唯一标识
        :param label: 节点的指令信息
        """
        if id not in self.adj_list:
            self.adj_list[id] = (label, [])

    def add_edge(self, from_id, to_id):
        """
        添加一条数据依赖边
        :param from_id: 依赖的起始节点 ID
        :param to_id: 目标节点 ID
        """
        if from_id in self.adj_list and to_id in self.adj_list:
            if to_id not in self.adj_list[from_id][1]:
                self.adj_list[from_id][1].append(to_id)

    def simplify(self):
        """
        简化图,去除多余依赖关系，如 A -> B, B -> C,A -> C, 则去除 A -> C
        """
        for from_id, (_, to_ids) in self.adj_list.items():
            to_ids_copy = to_ids.copy()
            for to_id in to_ids_copy:
                for to_id2 in to_ids_copy:
                    if to_id != to_id2 and to_id2 in self.adj_list[to_id][1]:
                        self.adj_list[from_id][1].remove(to_id2)
        return self
    
    def to_NetworkX(self):
        """
        转换为 NetworkX 图对象, 邻接矩阵形式
        """
        # 首先创建一个空的有向图，结点数量为 self.node_count
        G = nx.DiGraph()
        G.add_nodes_from(range(self.node_count))
        # 添加边
        for from_id, (_, to_ids) in self.adj_list.items():
            for to_id in to_ids:
                G.add_edge(from_id, to_id)
        return G
    

    def to_dot(self):
        """
        转换为 DOT 格式(Graphviz 可视化格式)
        """
        dot_str = "digraph DataDependency {\n"
        for node_id, (label, _) in self.adj_list.items():
            dot_str += f'  {node_id} [label="{label}"];\n'
        for from_id, (_, to_ids) in self.adj_list.items():
            for to_id in to_ids:
                dot_str += f"  {from_id} -> {to_id};\n" 
        dot_str += "}"
        return dot_str

    def __repr__(self):
        return f"Graph({len(self.adj_list)} nodes)"
    

def build_graph_from_dot(dot_str, mark):
    if mark == "wassail":
        return build_graph_from_dot_wassail(dot_str)
    elif mark == "wasma":
        return build_graph_from_dot_wasma(dot_str)
    elif mark == "binaryen":
        return build_graph_from_dot_wasmOpt(dot_str)
    else:
        raise ValueError(f"Unknown mark: {mark}")
    
def extract_all_instr_from_label(label):
    """
    解析节点 label，提取所有指令（去掉 instrX: 前缀）
    :param label: DOT 节点的 label 字符串
    :return: 纯指令列表 [指令1, 指令2, ...]
    """
    pattern = r"<instr\d+>(\d+:[^<\\\|]+)"  # 匹配 `<instrX>` 及指令内容
    return [instr.strip() for instr in re.findall(pattern, label)]  

    
def build_graph_from_dot_wassail(dot, count=0):
    """
    从 wassail 的输出中构建数据依赖图
    """
    ret = Graph(count, dot)
    graph = pydot.graph_from_dot_file(dot)[0]  # 解析 DOT 图
    for node in graph.get_nodes():
        insList = extract_all_instr_from_label(node.get_label())  # 提取节点指令
        for instr in insList:
            instrTuple = instr.split(":")
            ret.add_node(int(instrTuple[0].strip()), instrTuple[1].strip())  # 添加节点
    for edge in graph.get_edges():
        pattern = r"block\d+:instr(\d+) -> block\d+:instr(\d+)"  # 匹配边
        match = re.match(pattern, edge.get_source() + " -> " + edge.get_destination())
        if match:
            from_id, to_id = match.groups()
            ret.add_edge(int(from_id), int(to_id))  # 添加边
    return nx.transitive_closure(ret.to_NetworkX())


def build_graph_from_dot_wasma(dot, count=0):
    """
    从 wasma 的输出中构建数据依赖图
    """
    ret = Graph(count, dot)
    graph = pydot.graph_from_dot_file(dot)[0]  # 解析 DOT 图
    nodePattern = r"\"#\d+\+(\d+):(.*?)\""  # 匹配节点
    for node in graph.get_nodes():
        match = re.match(nodePattern, node.get_label())
        if match:
            instr_id, instr_content = match.groups()
            ret.add_node(int(instr_id), instr_content.strip())  # 添加节点
    for edge in graph.get_edges():
        pattern = r"(\d+) -> (\d+)"  # 匹配边
        match = re.match(pattern, edge.get_source() + " -> " + edge.get_destination())
        if match:
            to_id, from_id = match.groups()
            ret.add_edge(int(from_id), int(to_id))  # 添加边
    return nx.transitive_closure(ret.to_NetworkX())


def build_graph_from_dot_wasmOpt_helper(graph: Graph, node_id: str, debugLocMap: dict, visited: set):
    visited.add(node_id)
    retSet = set()
    for to_id in graph.adj_list[node_id][1]:
        if to_id in debugLocMap:
            retSet.add(to_id)
        else:
            if to_id in visited:
                continue
            s = build_graph_from_dot_wasmOpt_helper(graph, to_id, debugLocMap, visited)
            # Union set
            retSet = retSet.union(s)
    visited.remove(node_id)
    return retSet

def build_graph_from_dot_wasmOpt(dot, count=0):
    """
    从 wasm-opt 的输出中构建数据依赖图
    """
    tmp = Graph()
    graph = pydot.graph_from_dot_file(dot)[0]  # 解析 DOT 图
    debugLocPattern = r"\".*?\| Line: (\d+) \|.*?\""  # 匹配 debugLoc
    debugLocMap = {}  # debugLoc 映射表, key: node_name, value: debugLoc
    for node in graph.get_nodes():
        node_name = node.get_name()
        node_debugLoc = node.get_attributes().get("debugLoc")  # 获取 debugLoc  # 添加节点
        if node_debugLoc:
            match = re.match(debugLocPattern, node_debugLoc)
            if match:
                # print(match.group())
                debugLoc = match.group(1)
                debugLocMap[node_name] = debugLoc
        label = node.get_label()
        tmp.add_node(node_name, label[1:len(label)-1])  # 添加节点
    # print(debugLocMap)    
    for edge in graph.get_edges():
        from_id = edge.get_source()
        to_id = edge.get_destination()
        tmp.add_edge(from_id, to_id)

    # 修正图
    ret = Graph(count, dot)
    visited = set()
    for node_id, _ in tmp.adj_list.items():
        if node_id in debugLocMap:
            ret.add_node(int(debugLocMap[node_id]), tmp.adj_list[node_id][0])
            s = build_graph_from_dot_wasmOpt_helper(tmp, node_id, debugLocMap, visited)
            # print(s)
            for to_id in s:
                if debugLocMap[node_id] != debugLocMap[to_id]: # 避免自反
                    ret.add_node(int(debugLocMap[to_id]), tmp.adj_list[to_id][0])
                    ret.add_edge(int(debugLocMap[node_id]), int(debugLocMap[to_id]))        
    return nx.transitive_closure(ret.to_NetworkX())


def get_edges_set(graph):
    """提取图的边，转换为集合"""
    return set((edge[0], edge[1]) for edge in graph.get_edges())

# def jaccard_similarity(graph1 :Graph, graph2 :Graph):
#     edges1 = get_edges_set(graph1)
#     edges2 = get_edges_set(graph2)
#     print(edges1)
#     print(edges2)
    
#     intersection = len(edges1 & edges2)
#     union = len(edges1 | edges2)
#     print(intersection, union)
    
#     return intersection / union if union != 0 else 1.0  # 避免除零


# def compareGraphs(graphs: list):
#     """
#     比较多个图的相似度
#     :param graphs: 图列表
#     :return: 相似度矩阵
#     """
#     num_graphs = len(graphs)
#     similarity_matrix = np.zeros((num_graphs, num_graphs))

#     # 两两计算 Jaccard 相似度
#     for (i, g1), (j, g2) in itertools.combinations(enumerate(graphs), 2):
#         sim = jaccard_similarity(g1, g2)
#         similarity_matrix[i, j] = similarity_matrix[j, i] = sim  # 矩阵对称

#     # 对角线为 1
#     np.fill_diagonal(similarity_matrix, 1.0)

#     return similarity_matrix

def compareAdjacentMatrix(graphs):
    """
    比较多个图的Frobenius 范数
    :param graphs: 图列表，每个图为networkx表示的邻接矩阵
    :return: 相似度矩阵
    """
    num_graphs = len(graphs)
    similarity_matrix = np.zeros((num_graphs, num_graphs))

    # 打印graphs
    # for g in graphs:
    #     print(nx.adjacency_matrix(g).toarray())

    # 两两计算 Frobenius 范数
    for (i, g1), (j, g2) in itertools.combinations(enumerate(graphs), 2):
        sim = np.linalg.norm(nx.adjacency_matrix(g1).toarray() - nx.adjacency_matrix(g2).toarray(), 'fro')
        similarity_matrix[i, j] = similarity_matrix[j, i] = sim  # 矩阵对称

    return similarity_matrix

