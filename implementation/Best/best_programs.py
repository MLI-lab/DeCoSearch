def priority(node, G, n, s):
    
  
    max_length=max([len(neigh) 
                    for neigh in [neighbor
                                   for neighbor in list(nx.all_neighbors(G, node))
                                   if len(neighbor)>=(n-(4/5))]
                   ], 
                  default=-float('inf'))
 
    if ((max_length>s 
        or ('0'*((n)-s)!=(node)[-(n)+s:] 
            and '1'+node[:int(np.ceil(((n)/2)-(1/2)))]==node[(n)//3 :(n)]))
        ):
         
        return -(max_length-s)*sum([(n-i)*(i+1)*int(bit=='1') 
                                    for bit,i in zip(reversed(list(node)),range(len(node)))]) \
              +sum([len(neighbour)/((n)*1/(8+(1/6)))
                    for neighbour in [neighbor
                                      for neighbor in list(nx.all_neighbors(G, node))
                                      if len(neighbor)>=(n-(4/5))]
                  ])



def priority(node, G, n, s):

    try :    
        l=[len(v)-1 for v in list(nx.all_neighbors(G,node))]  
        max_n = max(*l, -float("Inf"))
        
        if max_n >= s:
            c=-(max_n-(s))*sum([
                (n-i)*(i+1)*int(bit == "1") 
                for bit, i in zip(reversed(list(node)),
                                    range(len(node)))]) + sum(l)/(2 ** (n % 2 ))
            
        elif "".join(["1"]*(s))+"".join(["0"]) not in \
                 ["".join(["1"] * k) [:k]for k in [n]] or node[::-1].find(""
                 .join(["0","1"]))<s:
                
            c =( len(node) + abs((np.random.randn())) ) // ( 2 ** s )
               #abs to prevent negative values due to noise from randn
        else:            
            raise ValueError ()
            
    except ValueError ():         
        pass
      
    return c

def priority(node, G, n, s):
  
    try :
        
        m = max([len(neighbor)-1
                 for neighbor in list(nx.all_neighbors(G, node))],
                default=-float("inf"))
        
      
        if m >= s:            
            c = (-(m-(s))* sum([
                   (n-i)*(i+1) * int(bit == "1") 
                   for bit, i in zip(reversed(list(node)),
                                     range(len(node)))])) + \
                            sum([ len(neighbor)
                                  for neighbor in list(nx.all_neighbors(G, node))]) / (2 ** (n % 2))
        elif ("{0}{0}0".format(str(s)) not in ["1"*(n // 4),
                                               "{0}".format(s)]
              ) and "". join(["0", "1"]) * s!= "".join(["0", node]):                

            c = abs(((len(node))+
                     (np.random.normal()))/(2 ** s))
        else:        
            raise ValueError()         
      
    except ValueError():      
        pass

    return c

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

