    MATCH (n:Neuron)-[:Contains]->(nss:SynapseSet)-[:Contains]->(ns:Synapse)
    WHERE n.type = 'Tm3'
    WITH ns, CASE
           WHEN exists(ns['ME(R)']) THEN ['ME', 'R']
           WHEN exists(ns['ME(L)']) THEN ['ME', 'L']
           WHEN exists(ns['LO(R)']) THEN ['LO', 'R']
           WHEN exists(ns['LO(L)']) THEN ['LO', 'L']
           WHEN exists(ns['LOP(R)']) THEN ['LOP', 'R']
           WHEN exists(ns['LOP(L)']) THEN ['LOP', 'L']
         END AS layerKey,
         count(ns) AS n_synapses
    RETURN
        ns.olHex1 AS hex1_dec,
        ns.olHex2 AS hex2_dec,
        ns.olLayer AS layer,
        layerKey[0] as region,
        layerKey[1] as side,
        sum(n_synapses) as total_synapses,
        count(DISTINCT ns.bodyId) as neuron_count
    ORDER BY hex1_dec, hex2_dec, layer
