#!/usr/bin/env python3
"""
Memory Enhancer - 记忆增强模块

功能：
1. 智能记忆关联 - 自动发现记忆之间的联系
2. 记忆压缩总结 - 使用 AI 压缩长记忆
3. 跨会话链接 - 连接相关会话的记忆
4. 知识网络 - 构建记忆关系图
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

# 记忆存储路径
MEMORY_DIR = "E:/openclaw/workspace/memory"
MEMORY_STATE_FILE = os.path.join(MEMORY_DIR, "memory-state.json")
MEMORY_ENHANCER_FILE = os.path.join(MEMORY_DIR, "memory-enhancer.json")


class MemoryEnhancer:
    """记忆增强器"""
    
    def __init__(self):
        self.memory_dir = MEMORY_DIR
        self.state_file = MEMORY_STATE_FILE
        self.enhancer_file = MEMORY_ENHANCER_FILE
        self.memories: Dict[str, Dict] = {}
        self.links: Dict[str, Set[str]] = defaultdict(set)  # 记忆链接
        self.sessions: Dict[str, Dict] = {}  # 会话关联
        self._load()
    
    def _load(self):
        """加载记忆数据"""
        # 加载增强器状态
        if os.path.exists(self.enhancer_file):
            with open(self.enhancer_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.links = defaultdict(set, data.get('links', {}))
                self.sessions = data.get('sessions', {})
        
        # 扫描记忆文件
        self._scan_memories()
    
    def _scan_memories(self):
        """扫描所有记忆文件"""
        if not os.path.exists(self.memory_dir):
            return
        
        for filename in os.listdir(self.memory_dir):
            if filename.endswith('.md') and filename != 'MEMORY.md':
                filepath = os.path.join(self.memory_dir, filename)
                memory_id = filename[:-3]  # 去掉 .md
                self.memories[memory_id] = self._parse_memory(filepath)
    
    def _parse_memory(self, filepath: str) -> Dict[str, Any]:
        """解析记忆文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取元数据
            meta = {
                'id': os.path.basename(filepath)[:-3],
                'filepath': filepath,
                'created': self._extract_date(content),
                'word_count': len(content),
                'topics': self._extract_topics(content),
                'entities': self._extract_entities(content)
            }
            
            return meta
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_date(self, content: str) -> Optional[str]:
        """提取日期"""
        # 从文件名或内容提取日期
        lines = content.split('\n')[:10]
        for line in lines:
            if '2026-' in line:
                return line.strip()
        return None
    
    def _extract_topics(self, content: str) -> List[str]:
        """提取主题关键词"""
        topics = []
        
        # 技术关键词
        tech_keywords = [
            'OpenClaw', '技能', 'memory', 'GitHub', 'Python',
            'AI', '模型', 'API', '数据库', '测试'
        ]
        
        content_lower = content.lower()
        for keyword in tech_keywords:
            if keyword.lower() in content_lower:
                topics.append(keyword)
        
        return topics[:10]  # 限制最多 10 个
    
    def _extract_entities(self, content: str) -> List[str]:
        """提取实体（人名、项目名等）"""
        entities = []
        
        # 简单提取：大写字母开头的词
        import re
        matches = re.findall(r'\b[A-Z][a-zA-Z0-9-]+\b', content)
        entities.extend(matches[:20])
        
        return list(set(entities))
    
    def find_related_memories(self, memory_id: str, limit: int = 5) -> List[Dict]:
        """查找相关记忆（基于主题和实体）"""
        if memory_id not in self.memories:
            return []
        
        target = self.memories[memory_id]
        target_topics = set(target.get('topics', []))
        target_entities = set(target.get('entities', []))
        
        related = []
        for mid, memory in self.memories.items():
            if mid == memory_id or 'error' in memory:
                continue
            
            # 计算相似度
            mem_topics = set(memory.get('topics', []))
            mem_entities = set(memory.get('entities', []))
            
            topic_overlap = len(target_topics & mem_topics)
            entity_overlap = len(target_entities & mem_entities)
            
            score = topic_overlap * 2 + entity_overlap * 3
            
            if score > 0:
                related.append({
                    'id': mid,
                    'score': score,
                    'common_topics': list(target_topics & mem_topics),
                    'common_entities': list(target_entities & mem_entities)
                })
        
        # 按分数排序
        related.sort(key=lambda x: x['score'], reverse=True)
        return related[:limit]
    
    def create_memory_link(self, from_id: str, to_id: str, link_type: str = 'related'):
        """创建记忆链接"""
        self.links[from_id].add(to_id)
        self.links[to_id].add(from_id)  # 双向链接
        self._save()
    
    def auto_link_memories(self, min_score: int = 3):
        """自动链接相关记忆"""
        linked_count = 0
        
        for mid1 in self.memories:
            related = self.find_related_memories(mid1, limit=10)
            for rel in related:
                if rel['score'] >= min_score:
                    mid2 = rel['id']
                    # 避免重复
                    if mid2 not in self.links[mid1]:
                        self.create_memory_link(mid1, mid2, 'auto-related')
                        linked_count += 1
        
        return linked_count
    
    def compress_memory(self, memory_id: str) -> Optional[str]:
        """压缩记忆（生成摘要）"""
        if memory_id not in self.memories:
            return None
        
        memory = self.memories[memory_id]
        
        # 简单压缩：提取关键信息
        summary_parts = []
        
        if memory.get('topics'):
            summary_parts.append(f"主题：{', '.join(memory['topics'][:3])}")
        
        if memory.get('entities'):
            summary_parts.append(f"实体：{', '.join(memory['entities'][:5])}")
        
        if memory.get('word_count'):
            summary_parts.append(f"长度：{memory['word_count']} 字")
        
        return ' | '.join(summary_parts) if summary_parts else None
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """获取会话上下文（包括相关记忆）"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'created': datetime.now().isoformat(),
                'memories': [],
                'summary': ''
            }
        
        session = self.sessions[session_id]
        
        # 获取关联的记忆
        related_memories = []
        for mem_id in session.get('memories', []):
            if mem_id in self.memories:
                related_memories.append({
                    'id': mem_id,
                    'topics': self.memories[mem_id].get('topics', []),
                    'compressed': self.compress_memory(mem_id)
                })
        
        return {
            'session_id': session_id,
            'memory_count': len(related_memories),
            'memories': related_memories,
            'summary': session.get('summary', '')
        }
    
    def add_memory_to_session(self, session_id: str, memory_id: str):
        """添加记忆到会话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'created': datetime.now().isoformat(),
                'memories': [],
                'summary': ''
            }
        
        if memory_id not in self.sessions[session_id]['memories']:
            self.sessions[session_id]['memories'].append(memory_id)
            self._save()
    
    def build_knowledge_network(self) -> Dict[str, Any]:
        """构建知识网络"""
        network = {
            'nodes': [],
            'edges': [],
            'stats': {
                'total_memories': len(self.memories),
                'total_links': sum(len(links) for links in self.links.values()) // 2,
                'isolated_memories': 0,
                'connected_components': 0
            }
        }
        
        # 添加节点
        for mid, memory in self.memories.items():
            if 'error' not in memory:
                network['nodes'].append({
                    'id': mid,
                    'topics': memory.get('topics', []),
                    'size': len(memory.get('entities', []))
                })
        
        # 添加边
        for from_id, to_ids in self.links.items():
            for to_id in to_ids:
                network['edges'].append({
                    'source': from_id,
                    'target': to_id
                })
        
        # 计算统计
        isolated = sum(1 for mid in self.memories if mid not in self.links or len(self.links[mid]) == 0)
        network['stats']['isolated_memories'] = isolated
        
        return network
    
    def _save(self):
        """保存增强器状态"""
        os.makedirs(os.path.dirname(self.enhancer_file), exist_ok=True)
        
        data = {
            'links': {k: list(v) for k, v in self.links.items()},
            'sessions': self.sessions,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.enhancer_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_enhanced_memory_report(self) -> Dict[str, Any]:
        """生成增强记忆报告"""
        network = self.build_knowledge_network()
        
        # 找出最关联的记忆
        most_linked = sorted(
            [(mid, len(links)) for mid, links in self.links.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_memories': network['stats']['total_memories'],
            'total_links': network['stats']['total_links'],
            'connected_memories': network['stats']['total_memories'] - network['stats']['isolated_memories'],
            'most_linked_memories': [
                {'id': mid, 'links': count} for mid, count in most_linked
            ],
            'topics_distribution': self._get_topics_distribution(),
            'recent_activity': self._get_recent_activity()
        }
    
    def _get_topics_distribution(self) -> Dict[str, int]:
        """获取主题分布"""
        topic_count = defaultdict(int)
        for memory in self.memories.values():
            for topic in memory.get('topics', []):
                topic_count[topic] += 1
        return dict(sorted(topic_count.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _get_recent_activity(self) -> List[str]:
        """获取最近活动"""
        recent = sorted(
            self.memories.keys(),
            key=lambda x: self.memories[x].get('created', '') or '',
            reverse=True
        )[:5]
        return recent


def main():
    """主函数 - 测试用"""
    enhancer = MemoryEnhancer()
    
    print("=" * 60)
    print("Memory Enhancer - 记忆增强报告")
    print("=" * 60)
    
    # 自动链接
    linked = enhancer.auto_link_memories()
    print(f"\n[自动链接] 创建了 {linked} 个新链接")
    
    # 生成报告
    report = enhancer.get_enhanced_memory_report()
    network = enhancer.build_knowledge_network()
    print(f"\n[记忆统计]")
    print(f"  总记忆数：{report['total_memories']}")
    print(f"  总链接数：{report['total_links']}")
    print(f"  已连接：{report['connected_memories']}")
    print(f"  孤立：{network['stats']['isolated_memories']}")
    
    print(f"\n[热门主题]")
    for topic, count in list(report['topics_distribution'].items())[:5]:
        print(f"  {topic}: {count}")
    
    print(f"\n[最关联的记忆]")
    for mem in report['most_linked_memories'][:3]:
        print(f"  {mem['id']}: {mem['links']} 个链接")
    
    # 构建知识网络
    network = enhancer.build_knowledge_network()
    print(f"\n[知识网络]")
    print(f"  节点数：{len(network['nodes'])}")
    print(f"  边数：{len(network['edges'])}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
