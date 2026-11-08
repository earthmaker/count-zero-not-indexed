"""Empty-answer discrimination experiment for the swegemma 0.2.7 graph tools, on a synthetic graph (not competition data).

Checks whether the three tools distinguish "does not exist" from "could not find". Positive controls (normal queries return non-empty) run first.
"""
import json, os, sys, tempfile
import numpy as np
from swegemma.graph import graph_utils as gu, embedding_utils as eu
from swegemma.tools import graph as tg

D = tempfile.mkdtemp()
REPO = 'toy/app'
g = gu.CustomMultiDiGraph()
g.graph['repo_name'] = REPO
# As in the competition graphs, the only edge type is lowercase 'calls' (measured: 452,588/452,588)
for n, txt in [('app.routes.get_user', 'def get_user(uid):\n    return load(uid)'),
               ('app.db.load', 'def load(uid):\n    return DB[uid]'),
               ('app.util.orphan', 'def orphan():\n    return 1')]:
    g.add_node(n, text=txt)
g.add_edge('app.routes.get_user', 'app.db.load', type='calls')
gpath = gu.save_graph_to_json(g, os.path.join(D, 'graphs'))
rng = np.random.default_rng(0)
emb = {n: rng.standard_normal(8).astype(np.float32) for n in g.nodes()}
epath = eu.save_embeddings_to_npz(REPO, emb, os.path.join(D, 'embeddings'))

class Ctx:  # only the attributes of the harness ctx that are needed
    repo = REPO
    task = {'repo': REPO}
    graph_dir = os.path.join(D, 'graphs')
    embeddings_dir = os.path.join(D, 'embeddings')
    max_stdout_chars = 5000
    def check_budget(self, count_tool_call=True):
        return None

def show(label, raw):
    r = json.loads(raw)
    keep = {k: r[k] for k in ('status', 'count') if k in r}
    if 'error_type' in r: keep['error_type'] = r['error_type']
    print(f'{label:<62} {json.dumps(keep, ensure_ascii=False)}')
    return r

c = Ctx()
print('== get_code_neighbors')
show('[positive] existing node with edges (get_user)', tg.get_code_neighbors(c, 'app.routes.get_user'))
show('[positive] existing node, edge_type="calls" (lowercase, as stored)', tg.get_code_neighbors(c, 'app.routes.get_user', 'calls'))
show('existing node, edge_type="CALLS" (as in the tool description example)', tg.get_code_neighbors(c, 'app.routes.get_user', 'CALLS'))
show('existing node, edge_type="IMPORTS" (in the description, absent from the data)', tg.get_code_neighbors(c, 'app.routes.get_user', 'IMPORTS'))
show('existing node without edges (orphan)', tg.get_code_neighbors(c, 'app.util.orphan'))
show('missing node (like an async def dropped from the graph)', tg.get_code_neighbors(c, 'app.routes.get_user_async'))
show('existing node by short name (get_user)', tg.get_code_neighbors(c, 'get_user'))
print('== search_similar_code')
show('[positive] exact node name', tg.search_similar_code(c, 'app.db.load', 2))
show('[positive] byte-identical node source', tg.search_similar_code(c, 'def load(uid):\n    return DB[uid]', 2))
show('short name (load)', tg.search_similar_code(c, 'load', 2))
show('natural-language query (function that loads a user from db)', tg.search_similar_code(c, 'function that loads a user from db', 2))
show('code fragment (one whitespace differs from source)', tg.search_similar_code(c, 'def load(uid):\n    return  DB[uid]', 2))
print('== get_code_subgraph')
show('[positive] two existing nodes', tg.get_code_subgraph(c, ['app.routes.get_user', 'app.db.load']))
show('two missing nodes', tg.get_code_subgraph(c, ['app.x.nope', 'app.y.nope']))
print('== subgraph full output')
print(tg.get_code_subgraph(c, ['app.routes.get_user', 'app.db.load'])[:400])
print(tg.get_code_subgraph(c, ['app.x.nope', 'app.y.nope'])[:400])
print(tg.get_code_neighbors(c, 'app.routes.get_user_async'))
print(tg.get_code_neighbors(c, 'app.util.orphan'))
