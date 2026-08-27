"""Data Structures & Algorithms fundamentals.

A compact reference implementation of the classics — sorting, searching,
graph traversal/shortest-path, and a few core data structures.
"""
from __future__ import annotations

import heapq
from collections import deque
from typing import Hashable


#  Searching

def binary_search(items: list[int], target: int) -> int:
    """Return the index of `target` in a sorted list, or -1."""
    lo, hi = 0, len(items) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if items[mid] == target:
            return mid
        if items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


#  Sorting

def quicksort(items: list[int]) -> list[int]:
    if len(items) <= 1:
        return items
    pivot = items[len(items) // 2]
    lesser = [x for x in items if x < pivot]
    equal = [x for x in items if x == pivot]
    greater = [x for x in items if x > pivot]
    return quicksort(lesser) + equal + quicksort(greater)


def merge_sort(items: list[int]) -> list[int]:
    if len(items) <= 1:
        return items
    mid = len(items) // 2
    left, right = merge_sort(items[:mid]), merge_sort(items[mid:])
    merged, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


# -------- Linked List

class ListNode:
    def __init__(self, value):
        self.value = value
        self.next: ListNode | None = None


class LinkedList:
    def __init__(self):
        self.head: ListNode | None = None

    def push(self, value) -> None:
        node = ListNode(value)
        node.next = self.head
        self.head = node

    def to_list(self) -> list:
        out, cur = [], self.head
        while cur:
            out.append(cur.value)
            cur = cur.next
        return out

    def reverse(self) -> None:
        prev = None
        cur = self.head
        while cur:
            cur.next, prev, cur = prev, cur, cur.next
        self.head = prev


# - Binary Search Tree

class BSTNode:
    def __init__(self, value):
        self.value = value
        self.left: BSTNode | None = None
        self.right: BSTNode | None = None


class BinarySearchTree:
    def __init__(self):
        self.root: BSTNode | None = None

    def insert(self, value) -> None:
        if self.root is None:
            self.root = BSTNode(value)
            return
        node = self.root
        while True:
            if value < node.value:
                if node.left is None:
                    node.left = BSTNode(value); return
                node = node.left
            else:
                if node.right is None:
                    node.right = BSTNode(value); return
                node = node.right

    def inorder(self) -> list:
        out = []

        def _walk(n: BSTNode | None):
            if n is None:
                return
            _walk(n.left)
            out.append(n.value)
            _walk(n.right)

        _walk(self.root)
        return out


#  Trie

class Trie:
    def __init__(self):
        self._root: dict = {}

    def insert(self, word: str) -> None:
        node = self._root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = True

    def search(self, word: str) -> bool:
        node = self._root
        for ch in word:
            if ch not in node:
                return False
            node = node[ch]
        return "$" in node


#  Graphs

Graph = dict[Hashable, list[tuple[Hashable, int]]]  # node -> [(neighbor, weight)]


def bfs(graph: Graph, start: Hashable) -> list[Hashable]:
    visited, order, queue = {start}, [], deque([start])
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor, _ in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return order


def dfs(graph: Graph, start: Hashable) -> list[Hashable]:
    visited, order = set(), []

    def _walk(node: Hashable) -> None:
        if node in visited:
            return
        visited.add(node)
        order.append(node)
        for neighbor, _ in graph.get(node, []):
            _walk(neighbor)

    _walk(start)
    return order


def dijkstra(graph: Graph, start: Hashable) -> dict[Hashable, float]:
    """Single-source shortest paths on a non-negatively weighted graph."""
    distances: dict[Hashable, float] = {start: 0}
    heap: list[tuple[float, Hashable]] = [(0, start)]
    visited: set[Hashable] = set()

    while heap:
        dist, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        for neighbor, weight in graph.get(node, []):
            new_dist = dist + weight
            if new_dist < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))

    return distances


# - UnionFind

class UnionFind:
    """Disjoint-set with path compression + union by rank."""

    def __init__(self, items: list[Hashable]):
        self._parent = {x: x for x in items}
        self._rank = {x: 0 for x in items}

    def find(self, x: Hashable) -> Hashable:
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])
        return self._parent[x]

    def union(self, a: Hashable, b: Hashable) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self._rank[ra] < self._rank[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        if self._rank[ra] == self._rank[rb]:
            self._rank[ra] += 1

    def connected(self, a: Hashable, b: Hashable) -> bool:
        return self.find(a) == self.find(b)