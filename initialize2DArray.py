# initialized the matrix of individual communication link probabilities for in- and out-gtroups
def initialize2DArray(inGroup, outGroup, n):
    frac = int(n/3)
    matrix = [[] for i in range(n)]
    for i in range(n):
        for j in range(n):
            if(i <= frac and j <= frac):
                matrix[i].append(inGroup)
            else:
                if(frac < i <= (frac * 2) and frac < j <= (frac * 2)):
                    matrix[i].append(inGroup)
                else:
                    if((frac * 2) < i <= (n - 1) and (frac * 2) < j <= (n - 1)):
                        matrix[i].append(inGroup)
                    else:
                        matrix[i].append(outGroup)
    return matrix
