# initialized the matrix of individual communication link probabilities for in- and out-gtroups
def initialize2DArray(inGroup, outGroup, n):
    matrix = [[] for i in range(n)]
    for i in range(n):
        for j in range(n):
            if(i <= 33 and j <= 33):
                matrix[i].append(inGroup)
            else:
                if(33 < i <= 66 and 33 < j <= 66):
                    matrix[i].append(inGroup)
                else:
                    if(66 < i <= 99 and 66 < j <= 99):
                        matrix[i].append(inGroup)
                    else:
                        matrix[i].append(outGroup)
    return matrix
