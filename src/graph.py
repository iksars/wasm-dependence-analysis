import re
import pydot
import itertools
import numpy as np
import networkx as nx
import concurrent.futures

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
                if (to_id >= self.node_count) or (from_id >= self.node_count):
                    continue
                G.add_edge(from_id, to_id)
        return G
    

    def to_dot(self):
        """
        转换为 DOT 格式(Graphviz 可视化格式)
        """
        dot_str = "digraph \"{}\" {{\n".format(self.orignate)
        for node_id, (label, _) in self.adj_list.items():
            dot_str += f'  {node_id} [label="{node_id}:{label}"];\n'
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


def merge_local_get_set(graph: Graph) -> Graph:
    """
    合并 local.get 和 local.set 指令
    :param graph: Graph 对象
    :return: 合并后的 Graph 对象
    """
    # 合并示例：
    # local.get $0 -> local.set $0 -> instr1 合并为 local.get $0 -> instr1
    # 定义一个映射表，用于存储每一句 local.get或local.set 和其最终的值
    local_map = {}
    # 遍历图的每个节点
    for node_id, _ in graph.adj_list.items():
        merge_local_get_set_helper(graph, node_id, local_map)
    # print(local_map)
    # 利用映射表更新图
    res = Graph(graph.node_count, graph.orignate)
    # 添加节点
    for node_id, (label, _) in graph.adj_list.items():
        if node_id in local_map:
            if local_map[node_id] == node_id:
                res.add_node(node_id, label)
            else:
                continue
        else:
            res.add_node(node_id, label)
    # 添加边
    for node_id, (_, to_ids) in graph.adj_list.items():
        if node_id in res.adj_list:
            for to_id in to_ids:
                if to_id in local_map:
                    res.add_edge(node_id, local_map[to_id])
                res.add_edge(node_id, to_id)
    return res

# def merge_local_get_set_helper(graph: Graph, node_id: int, local_map: dict) -> int:
#     # 如果节点不是 local.get 或 local.set, 直接返回
#     if "local.get" not in graph.adj_list[node_id][0] and "local.set" not in graph.adj_list[node_id][0]:
#         return node_id
#     # 如果节点是 local.get 或 local.set, 先判断是否已经合并过
#     if node_id in local_map:
#         return local_map[node_id]
#     else:
#         # 如果没有后继节点, 直接返回
#         if not graph.adj_list[node_id][1]:
#             local_map[node_id] = node_id
#             return node_id
#         # 如果有后继节点, 合并后继节点
#         res = merge_local_get_set_helper(graph, graph.adj_list[node_id][1][0], local_map)
#         local_map[node_id] = res
#         return res

def merge_local_get_set_helper(graph: Graph, node_id: int, local_map: dict):
    path = []
    current = node_id

    # 迭代找最终合并目标
    while True:
        # 检查path中是否有当前节点，如果有，说明有环，直接返回
        if current in path:
            for node in path:
                local_map[node] = node
        label, successors = graph.adj_list[current]
        if "local.get" not in label and "local.set" not in label:
            break
        if current in local_map:
            current = local_map[current]
            break
        path.append(current)
        if not successors:
            break
        current = successors[0]

    # 路径压缩
    for node in path:
        local_map[node] = current

    
    
def build_graph_from_dot_wassail(dot, count=0):
    """
    从 wassail 的输出中构建数据依赖图
    """
    ret = Graph(count, dot)
    try:
        graph = pydot.graph_from_dot_file(dot)[0]  # 解析 DOT 图
        for node in graph.get_nodes():
            insList = extract_all_instr_from_label(node.get_label())  # 提取节点指令
            for instr in insList:
                instrTuple = instr.split(":")
                if len(instrTuple) != 2:
                    raise ValueError(f"Invalid instruction format: {instr}")
                if instrTuple[1].strip() == "return": # 跳过 return 指令
                    continue
                ret.add_node(int(instrTuple[0].strip()), instrTuple[1].strip())  # 添加节点
        for edge in graph.get_edges():
            pattern = r"block\d+:instr(\d+) -> block\d+:instr(\d+)"  # 匹配边
            match = re.match(pattern, edge.get_source() + " -> " + edge.get_destination())
            if match:
                from_id, to_id = match.groups()
                ret.add_edge(int(from_id), int(to_id))  # 添加边
    except Exception as e:
        print(f"Error parsing DOT file: {e}")
        return Graph(count, dot)  # 返回空图
    
    return merge_local_get_set(ret) 


def build_graph_from_dot_wasma(dot, count=0):
    """
    从 wasma 的输出中构建数据依赖图
    """
    ret = Graph(count, dot)
    try: 
        graph = pydot.graph_from_dot_file(dot)[0]  # 解析 DOT 图
        nodePattern = r"\"#\d+\+(\d+):(.*?)\""  # 匹配节点
        localPattern = r"\"#\d+: \((local|param|global) (.*?)\)\""  # 匹配 local变量
        localMap = {}  # local变量映射表,key: local变量名, value: ([前驱节点列表],[后继节点列表])
        weightMap = {}  # 权重映射表,key: (from_id, to_id), value: weight
        # 规则：
        # 1. 1对1，如 local.set 0 -> L0 -> local.get 0,直接传递
        # 2. 1对多，如 local.set 0 -> L0 -> local.get 01, local.get 02,直接传递
        # 3. 多对1，如 local.set 01, local.set 02 -> L0 -> local.get 0,需要判断local.get的值到底来自于哪个local.set，判断规则如下：
        #   如果与L0相连的边上有权重，按照权重相等来传递，若无，按照间接边上的权来传递，如 a ->(va) local.set 01 ->(va) L0 -> local.get 0 ->(va) b
        #   如果无法判断，报错
        # 4. 多对多，需对于每个local.get都要进行多对1的判断
        for node in graph.get_nodes():
            match = re.match(nodePattern, node.get_label())
            if match:
                instr_id, instr_content = match.groups()
                ret.add_node(int(instr_id), instr_content.strip())  # 添加节点
            match2 = re.match(localPattern, node.get_label())
            if match2:
                local_id = match2.group(2)
                # print(local_id)
                if local_id not in localMap:
                    localMap[local_id] = ([], [])
        # print(localMap)
        for edge in graph.get_edges():
            pattern = r"(\d+) -> (\d+)"  # 匹配边
            match = re.match(pattern, edge.get_source() + " -> " + edge.get_destination())
            if match:
                to_id, from_id = match.groups()
                ret.add_edge(int(from_id), int(to_id))  # 添加边
            if edge.get_source() in localMap:
                localMap[edge.get_source()][1].append(edge.get_destination())
            if edge.get_destination() in localMap:
                localMap[edge.get_destination()][0].append(edge.get_source())
            weight = edge.get_label()
            if weight:
                weightMap[(edge.get_source(), edge.get_destination())] = weight
        # print(weightMap)
        for local_id, (from_ids, to_ids) in localMap.items():
            # print(local_id, from_ids, to_ids)
            if len(from_ids) == 1 and len(to_ids) == 1:
                ret.add_edge(int(to_ids[0]), int(from_ids[0]))
            elif len(from_ids) == 1 and len(to_ids) > 1:
                for to_id in to_ids:
                    # print("to_id", to_id, "from_ids", from_ids[0])
                    ret.add_edge(int(to_id), int(from_ids[0]))
            elif len(from_ids) > 1 and len(to_ids) == 1:
                build_graph_from_dot_wasma_helper(ret, to_ids[0], weightMap, localMap, local_id)
            elif len(from_ids) > 1 and len(to_ids) > 1:
                for to_id in to_ids:
                    build_graph_from_dot_wasma_helper(ret, to_id, weightMap, localMap, local_id)
    except Exception as e:
        print(f"Error parsing DOT file: {e}")
        return Graph(count, dot)
    return merge_local_get_set(ret)  # 合并 local.get 和 local.set 指令

def build_graph_from_dot_wasma_helper(graph: Graph, node_id: str, weightMap: dict, localMap: dict, local_id: str):
    # print("build_graph_from_dot_wasma_helper", node_id, local_id)
    # print("localMap", localMap)
    # print("weightMap", weightMap)
    # 帮助一个后继节点找到它的前驱节点
    from_ids = localMap[local_id][0] 
    if (local_id, node_id) in weightMap:
        weight = weightMap[(local_id, node_id)]
        last_m = ""
        cur_m = ""
        for from_id in from_ids:
            if (from_id, local_id) in weightMap and weightMap[(from_id, local_id)] == weight:
                last_m = cur_m
                cur_m = from_id
        if cur_m == "":
            # not found, nothing to do
            pass
        else:
            if last_m == "":
                graph.add_edge(int(node_id), int(cur_m))
                return
            else:
                # 多个前驱节点，不能确定
                # TODO: 处理这种情况
                pass
    else:
        # 如果没有权重，先找间接边
        for pair in weightMap:
            if pair[0] == node_id:
                weight = weightMap[pair]
                last_m = ""
                cur_m = ""
                for from_id in from_ids:
                    if (from_id, local_id) in weightMap and weightMap[(from_id, local_id)] == weight:
                        last_m = cur_m
                        cur_m = from_id
                if cur_m == "":
                    # not found, nothing to do
                    pass
                else:
                    if last_m == "":
                        graph.add_edge(int(node_id), int(cur_m))
                        return
                    else:
                        # 多个前驱节点，不能确定
                        # TODO: 处理这种情况
                        pass
        # 如果没有间接边，找到唯一的无权前驱
        last_m = ""
        cur_m = ""
        for from_id in from_ids:
            if (from_id, local_id) not in weightMap:
                last_m = cur_m
                cur_m = from_id
        if cur_m == "":
            # not found, nothing to do
            pass    
        else:
            if last_m == "":
                graph.add_edge(int(node_id), int(cur_m))
                return
            else:
                # 多个前驱节点，不能确定
                # TODO: 处理这种情况
                pass


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
    try:
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
    except Exception as e:
        print(f"Error parsing DOT file: {e}")
        return Graph(count, dot)  
    return ret


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

# def compareAdjacentMatrix(graphs):
#     """
#     比较多个图的Frobenius 范数
#     :param graphs: 图列表，每个图为networkx表示的邻接矩阵
#     :return: 相似度矩阵
#     """
#     num_graphs = len(graphs)
#     similarity_matrix = np.zeros((num_graphs, num_graphs))

#     # for g in graphs:
#     #     print(g.node_count)

#     # 两两计算 Frobenius 范数
#     for (i, g1), (j, g2) in itertools.combinations(enumerate(graphs), 2):
#         sim = np.linalg.norm(nx.adjacency_matrix(g1.to_NetworkX()).toarray() - nx.adjacency_matrix(g2.to_NetworkX()).toarray(), 'fro')
#         similarity_matrix[i, j] = similarity_matrix[j, i] = sim  # 矩阵对称

#     return similarity_matrix

def _frobenius_task(args):
    i, j, g1, g2 = args
    m1 = nx.adjacency_matrix(g1.to_NetworkX()).toarray()
    m2 = nx.adjacency_matrix(g2.to_NetworkX()).toarray()
    sim = np.linalg.norm(m1 - m2, 'fro')
    return i, j, sim

def compareAdjacentMatrix(graphs):
    """
    并行计算多个图的 Frobenius 范数差异
    :param graphs: 图列表，每个图为 networkx 表示的邻接矩阵
    :return: 相似度矩阵（对称）
    """
    num_graphs = len(graphs)
    similarity_matrix = np.zeros((num_graphs, num_graphs))

    args_list = [
        (i, j, graphs[i], graphs[j])
        for (i, g1), (j, g2) in itertools.combinations(enumerate(graphs), 2)
    ]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(_frobenius_task, args_list)

    for i, j, sim in results:
        similarity_matrix[i, j] = similarity_matrix[j, i] = sim

    return similarity_matrix

def f(tmp: Graph, debugLocMap: map):
    ret = Graph()
    visited = set()
    for node_id, _ in tmp.adj_list.items():
        if node_id in debugLocMap:
            ret.add_node(int(debugLocMap[node_id]), tmp.adj_list[node_id][0])
            s = build_graph_from_dot_wasmOpt_helper(tmp, node_id, debugLocMap, visited)
            for to_id in s:
                if debugLocMap[node_id] != debugLocMap[to_id]: # 避免自反
                    ret.add_node(int(debugLocMap[to_id]), tmp.adj_list[to_id][0])
                    ret.add_edge(int(debugLocMap[node_id]), int(debugLocMap[to_id])) 
    return ret
    