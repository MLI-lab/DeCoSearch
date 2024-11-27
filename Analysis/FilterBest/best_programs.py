def priority(node, G, n, s):

    neighbors = list(nx.all_neighbors(G, node))
    L = [len(v)-1 for v in neighbors]

    M = max(-float("inf"), *L)
    if M >= s and any([k[~0] == '1' for k in neighbors]):        
        P = -sum([(M - (s))*( (n-i)*(i+1)*int(j=='1') ) 
            for i,j in enumerate( reversed(node) ) ]) / \
               (((1 + (s) + (s)**2) + ( (n - s) // 3)**3 )) +\
                  len(neighbors)/5        
    elif M < s :
        
        if all( [len(k)==1 or k[~0]== '1'] for k in neighbors ):
            
            P = int( ''.join(['1'*k for k,_ in filter(lambda x: x[0][-1]=='1',enumerate(node))] ), base=2)\
                 /((n//3)**3)+ len(neighbors)

        else:            

            P = None
        
    else:       
        P = None       
    
    return P

