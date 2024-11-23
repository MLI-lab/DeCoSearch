def priority(node, G, n, s):

    if node=="0"*(n-s):return float('Inf')
    
    neighbors=[neighbor 
              for neighbor in list(nx.all_neighbors(G,node))] 
    
    max_neighbor_length=min([len(neigh)for neigh in neighbors],default=-float('inf')) 
    return -(max_neighbor_length-s)*sum([(n-i)*(i+1)*int(bit=='1') 
                                        for i, bit in enumerate(reversed(list(node)))])+sum([len(neigh)/(n*1/48)
                                                                                            for neigh in neighbors])/8

def priority(node, G, n, s):
    #get all possible neighbors whose lengths>=n 
    neighbors=[neighbor
               for neighbor in list(nx.all_neighbors(G, node)) 
               if len(neighbor)>=(n-s)] 

    max_neighbor_length= min([len(neigh)
                              for neigh in neighbors],default=-float("inf"))
    #Add heuristic checks to prioritize adding of specific sets of nodes
   
    if ((max_neighbor_length >s )or 
        ("0"*((n)-s)!="".join(list(node)[-(n)+s:])
         and ("1"+node[:int(np.floor(((n)/2))+(1/8))]== "".join(list(node)[(n)//3:(n)])))):
        
        # Add weights based on lengths of neighbors
        return -(max_neighbor_length-s)\
                *(
                    sum([(n-i)*(i+1)*int(bit=="1")
                         for i, bit in enumerate(reversed(list(node)))]
                       )) \
              + sum([len(neigh)/(n*1/(6.9))
                     for neigh in neighbors 
                    ] 
                   )

def priority(node, G, n, s):

    if node == "0" * (n - s): #if string is all zeros then priority will be infinity 
        return float("inf")

    neighbors=[neighbor 
               for neighbor
               in list(nx.all_neighbors(G, node))
                  ]
    
    max_neighbor_length=min([len(neigh)
                             for neigh
                            in neighbors
                                ], default=float('-inf'))
    return (-(max_neighbor_length - s))*sum([(n-i)*(i+1)\
                                            *int(bit=="1") 
                                              for i,\
                                                bit \
                                                    in enumerate(\
                                                        reversed(list(node)))])+sum([len(neigh)/(n*8/45)
                                                                                    for neigh 
                                                                                in neighbors
                                                                                 ])    
    h(G, node)



def priority(node, G, n, s):

    if node[-3:]!= '0'*s:
        neighbors=[neighbor 
                   for neighbor in list(nx.all_neighbors(G, node))]
        
        #if all(neighbor[0:(n-s)]=='0' 
        #       and any([neigh==node[:n-(s)+1]+'1'+node[(n-s)+2:]]
        #              )for neighbor in neighbors), use this statement instead
        return (-(max((len(neigh)
                       for neigh in neighbors
                      ),default=(n-s))
                )*
               sum((((n-i)*(i+1)*
                     int(bit=="1")
                    ) 
                    for i, bit in enumerate(reversed(list(node))))
                  ))+\
              sum(([len(neigh)/((n*1/8)**2)
                   for neigh in neighbors]))
