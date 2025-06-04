"""
A node path that can be searched upon a node map/tree
TODO: include with paths
"""
import typing
import re


class InvalidNodePath(IndexError):
    """
    Raised when an invalid path is encountered
    """

NodeLike=typing.Any
PathStepType=typing.Union[str,typing.Pattern]
PathCompatible=typing.Union[str,typing.Iterable[PathStepType]]
class NodePath:
    """
    A node path that can be searched upon a node map/tree
    TODO: include with paths
    """
    def __init__(self,
        path:PathCompatible,
        ignoreCase:bool=False,
        matchStyle:str='glob',
        separator:str='/',
        allowDoubleStar:bool=True):
        """
        :ignoreCase: perform case-insensitive matching
        :matchStyle:
            'glob': supports glob-style matching (see below)
            'regex': supports regex-style matching
            'strict': strict,verbatim matching

        Regex style supports:
            standard python regex but with separator preserved
            like /a/b(c/[a-z]*)+/e
            "**": match any sequence of nodes if allowDoubleStar
                (like recursive wildcard in glob).

        Glob style supports:
            "a": literal match.
            "..": parent of the current node.
            "*": match any single node at this level.
            "**": match any sequence of nodes if allowDoubleStar
                (like recursive wildcard in glob).
            ".": current node.
            leading "/": to start at root node.
        """
        self._separator=separator
        self._ignoreCase=ignoreCase
        self._matchStyle=matchStyle
        self._allowDoubleStar=allowDoubleStar
        self._parts:typing.List[PathStepType]=[]
        self.assign(path,ignoreCase,
            matchStyle,separator,allowDoubleStar)

    def __len__(self)->int:
        return len(self._parts)

    def __iter__(self)->PathStepType:
        return iter(self._parts)

    def assign(self,
        path:PathCompatible,
        ignoreCase:bool=False,
        matchStyle:str='glob',
        separator:str='/',
        allowDoubleStar:bool=True
        )->None:
        """
        Assign the value of this path

        This also splits a regex path into path segments
        while preserving grouping.

        Special '**' means match any number of segments.
        """
        self._separator=separator
        self._ignoreCase=ignoreCase
        self._matchStyle=matchStyle
        self._allowDoubleStar=allowDoubleStar
        if not isinstance(path,str):
            # simplest way is to just copy whatever as our path
            self._parts=list(path)
        elif matchStyle=='strict':
            self._parts=path.split(self._separator)
        elif matchStyle=='glob':
            self._parts=path.split(self._separator)
            if path[0]==self._separator:
                self._parts.insert(0,'')
        else:
            segments=[]
            current=''
            depth=0
            escape=False
            i=0
            if path.startswith(self._separator):
                self._parts.insert(0,'')
                i=1  # skip initial '/'
            while i<len(path):
                char=path[i]
                if escape:
                    current+=char
                    escape=False
                elif char==self._separator:
                    current+=char
                    escape=True
                elif char=='(':
                    current+=char
                    depth+=1
                elif char==')':
                    current+=char
                    depth -=1
                elif char==self._separator and depth==0:
                    if allowDoubleStar and current=='**':
                        segments.append('**')  # special token
                    else:
                        current=re.compile(rf'^{current}$')
                        segments.append(current)
                    current=''
                else:
                    current+=char
                i+=1
            if current:
                if allowDoubleStar and current=='**':
                    segments.append('**')
                else:
                    current=re.compile(rf'^{current}$')
                    segments.append(current)
            if depth !=0:
                raise ValueError("Unbalanced parentheses in path regex")
        return segments

    def getNodes(self,
        startingNode:NodeLike,
        ignore:typing.Optional[typing.Set[NodeLike]]=None,
        pathStack:typing.Optional[typing.Set[NodeLike]]=None,
        allowRecurseAboveStart:bool=False
        )->typing.Generator[NodeLike,None,None]:
        """
        Recursively search for all paths in the tree
        that match the wildcard path.

        This has built-in logic to prevent getting caught in loops.
        """
        if pathStack is None:
            pathStack=set()
        if ignore is None: # ignore is also used to prevent loops
            ignore=set()
        strict=self._matchStyle=='strict'
        def _getNodeByPath(root:NodeLike,path:PathStepType)->NodeLike:
            """
            Helper to navigate a tree node path to a node object.
            """
            node=root
            for part in path[1:]:  # skip root
                node=node.children.get(part)
                if node is None:
                    return None
            return node
        def _search(
            currentNode:NodeLike,
            parts:typing.Iterable[PathStepType],
            stack:typing.Set[NodeLike]
            )->typing.Generator[typing.Iterable[NodeLike],None,None]:
            """
            Search at a given location
            """
            if currentNode in ignore:
                return
            ignore.add(currentNode)
            if not parts:
                yield stack.copy()
                return
            part=parts[0]
            if isinstance(part,re.Pattern):
                for childName,child in currentNode.children.items():
                    if part.match(childName):
                        yield from _search(child,parts[1:],stack+[childName])
            elif part==".." and not strict:
                # go up one, but avoid traversing above root
                if len(stack)>1 or allowRecurseAboveStart:
                    parent_stack=stack[:-1]
                    parent_node=_getNodeByPath(startingNode,parent_stack)
                    yield from _search(parent_node,parts[1:],parent_stack)
            elif part=="**" and self._allowDoubleStar and not strict:
                # Match current level and all deeper levels
                yield from _search(currentNode,parts[1:],stack) # Match 0-level
                for childName,child in currentNode.children.items():
                    yield from _search(child,parts,stack+[childName])
            elif part=="*" and not strict:
                # take all children
                for childName,child in currentNode.children.items():
                    yield from _search(child,parts[1:],stack+[childName])
            elif part=="." and not strict:
                # just the current path, so do nothing
                yield from _search(currentNode,parts[1:],stack)
            else:
                # a normal path name
                if part in currentNode.children:
                    yield from _search(
                        currentNode.children[part],parts[1:],stack+[part])
        parts=self._parts
        if not parts[0]:
            # if it started with '/'
            parts=parts[1:]
            startingNode=startingNode.root
        yield from _search(startingNode,parts,pathStack or [startingNode.name])
    search=getNodes

    def __repr__(self):
        return self._separator.join([str(p) for p in self._parts])
