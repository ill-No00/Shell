




class Trie:
    
    def __init__(self):
        
        self.trie = {}
    
    def insert(self,word):
        
        d = self.trie
        
        for c in word:
            if c not in d:
                d[c] ={}
            d = d[c]
        
        d['.'] = '.'
    
    def search(self,word):
        d = self.trie
        
        for c in word:
            if c not in d:
                return False
            d = d[c]
        
        return '.' in d   
     
    def startsWith(self,prefix):
        d = self.trie
        
        for c in prefix:
            if c not in d:
                return False
            d = d[c]
            
        return True
    
    def autoComplete(self,prefix):
        d = self.trie
        
        for c in prefix:
            if c in d:
                d = d[c]
            else:
                return []
        
        result = []
        
        self._dfs(d,prefix,result)
        
        return result
    
    def _dfs(self,d,current_word,result):
        
        if '.' in d:
            result.append(current_word)
            
        for c in d:
            if c == '.':
                continue
            self._dfs(d[c],current_word+c,result)
            