-- Exportar chamados do 1746 a partir de 2023-01-01
SELECT
  id_chamado,
  data_inicio,
  data_fim,
  data_alvo_finalizacao,
  tipo,
  subtipo,
  status,
  situacao,
  longitude,
  latitude,
  data_particao
FROM `datario.adm_central_atendimento_1746.chamado`
WHERE data_particao >= '2023-01-01';
