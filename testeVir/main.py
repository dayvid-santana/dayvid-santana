from libs.conecta_externamente import ConexaoOracle
from libs.toml_configuracoes import ConfigsToml

tom = ConfigsToml('dadosConexoes')
cred = tom.acessarDadosToml('BdOracle')
conn = ConexaoOracle(cred, cred['rpa_dre'])




# result = conn.executarDql('select * from giga.vendas where rownum <= 100')
# print(result)

