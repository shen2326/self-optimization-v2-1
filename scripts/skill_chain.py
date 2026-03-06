#!/usr/bin/env python3
"""
技能链框架 - Skill Chain Framework

让技能可以调用其他技能
"""

import os
import json
import importlib.util
from typing import Dict, List, Any, Optional, Set

# 技能目录
SKILLS_DIR = "E:/openclaw/workspace/skills"
SKILL_INDEX_FILE = os.path.join(SKILLS_DIR, "skill-index.json")


class SkillChain:
    """技能链管理器"""
    
    def __init__(self):
        self.skills_dir = SKILLS_DIR
        self.index_file = SKILL_INDEX_FILE
        self.skill_index: Optional[Dict] = None
        self.loaded_modules: Dict[str, Any] = {}
        self.skill_dependencies: Dict[str, List[str]] = {}
        self._load_index()
    
    def _load_index(self):
        """加载技能索引"""
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.skill_index = json.load(f)
    
    def get_skill_path(self, skill_name: str) -> Optional[str]:
        """获取技能路径"""
        skills = self.skill_index.get('skills', {})
        
        # 直接查找
        if skill_name in skills:
            return skills[skill_name].get('path')
        
        # 模糊查找
        for key, info in skills.items():
            if info.get('name', '').lower() == skill_name.lower():
                return info.get('path')
        
        return None
    
    def load_skill(self, skill_name: str) -> Optional[Any]:
        """加载技能模块"""
        # 检查是否已加载
        if skill_name in self.loaded_modules:
            return self.loaded_modules[skill_name]
        
        # 获取技能路径
        skill_path = self.get_skill_path(skill_name)
        if not skill_path:
            print(f"[ERROR] 技能不存在：{skill_name}")
            return None
        
        # 查找技能的主模块
        main_module = None
        for module_name in ['main.py', 'skill.py', 'coordinator.py']:
            module_path = os.path.join(skill_path, module_name)
            if os.path.exists(module_path):
                main_module = module_path
                break
        
        if not main_module:
            print(f"[WARN] 技能 {skill_name} 没有主模块文件")
            return None
        
        # 动态加载模块
        try:
            spec = importlib.util.spec_from_file_location(skill_name, main_module)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self.loaded_modules[skill_name] = module
            print(f"[OK] 加载技能：{skill_name}")
            return module
        except Exception as e:
            print(f"[ERROR] 加载技能失败 {skill_name}: {e}")
            return None
    
    def call_skill(self, skill_name: str, function_name: str, *args, **kwargs) -> Any:
        """调用技能的函数"""
        # 加载技能
        module = self.load_skill(skill_name)
        if not module:
            return None
        
        # 获取函数
        if not hasattr(module, function_name):
            print(f"[ERROR] 技能 {skill_name} 没有函数 {function_name}")
            return None
        
        func = getattr(module, function_name)
        
        # 调用函数
        try:
            result = func(*args, **kwargs)
            print(f"[OK] 调用 {skill_name}.{function_name}() 成功")
            return result
        except Exception as e:
            print(f"[ERROR] 调用 {skill_name}.{function_name}() 失败：{e}")
            return None
    
    def chain_skills(self, chain_config: List[Dict]) -> Any:
        """
        执行技能链
        
        chain_config: [
            {'skill': 'github', 'function': 'fetch_trending', 'args': []},
            {'skill': 'data-analysis', 'function': 'analyze', 'args': ['previous']},
            {'skill': 'matplotlib', 'function': 'visualize', 'args': ['previous']},
        ]
        """
        previous_result = None
        
        for step in chain_config:
            skill_name = step.get('skill')
            function_name = step.get('function')
            args = step.get('args', [])
            
            # 替换 'previous' 为上一步结果
            if 'previous' in args:
                args = [previous_result if a == 'previous' else a for a in args]
            
            # 调用技能
            result = self.call_skill(skill_name, function_name, *args)
            
            if result is None:
                print(f"[ERROR] 技能链中断于：{skill_name}.{function_name}")
                return None
            
            previous_result = result
        
        return previous_result
    
    def get_skill_dependencies(self, skill_name: str) -> List[str]:
        """获取技能的依赖列表"""
        # 从 SKILL.md 中解析依赖
        skill_path = self.get_skill_path(skill_name)
        if not skill_path:
            return []
        
        skill_md = os.path.join(skill_path, 'SKILL.md')
        if not os.path.exists(skill_md):
            return []
        
        dependencies = []
        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析 YAML frontmatter 中的 dependencies
            import re
            frontmatter_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                deps_match = re.search(r'dependencies:\s*\n((?:\s+-\s+\w+[\s\S]*?))', frontmatter)
                if deps_match:
                    deps_text = deps_match.group(1)
                    dependencies = re.findall(r'-\s+(\w+[\-\w]*)', deps_text)
        except Exception as e:
            print(f"[WARN] 解析依赖失败 {skill_name}: {e}")
        
        return dependencies
    
    def load_skill_with_deps(self, skill_name: str) -> Optional[Any]:
        """加载技能及其依赖"""
        # 先加载依赖
        deps = self.get_skill_dependencies(skill_name)
        for dep in deps:
            if dep not in self.loaded_modules:
                print(f"[INFO] 加载依赖：{dep}")
                self.load_skill(dep)
        
        # 加载主技能
        return self.load_skill(skill_name)


# 全局实例
_chain_instance: Optional[SkillChain] = None

def get_chain() -> SkillChain:
    """获取全局技能链实例"""
    global _chain_instance
    if _chain_instance is None:
        _chain_instance = SkillChain()
    return _chain_instance

def call(skill: str, func: str, *args, **kwargs) -> Any:
    """便捷函数：调用其他技能"""
    return get_chain().call_skill(skill, func, *args, **kwargs)

def chain(steps: List[Dict]) -> Any:
    """便捷函数：执行技能链"""
    return get_chain().chain_skills(steps)


# 测试
def main():
    """测试技能链"""
    print("=" * 70)
    print("技能链框架 - 测试")
    print("=" * 70)
    
    chain_mgr = SkillChain()
    
    # 测试 1: 加载技能
    print("\n[测试 1] 加载技能")
    print("-" * 50)
    
    test_skills = ['github', 'data-analysis', 'matplotlib']
    for skill in test_skills:
        module = chain_mgr.load_skill(skill)
        if module:
            print(f"  [OK] {skill} loaded")
        else:
            print(f"  [FAIL] {skill} failed")
    
    # 测试 2: 获取依赖
    print("\n[Test 2] Get Dependencies")
    print("-" * 50)
    
    test_skill = 'github-analysis-report'
    deps = chain_mgr.get_skill_dependencies(test_skill)
    print(f"  {test_skill} deps: {deps}")
    
    # 测试 3: 技能链
    print("\n[Test 3] Skill Chain")
    print("-" * 50)
    
    test_chain = [
        {'skill': 'github', 'function': 'fetch_data', 'args': ['python']},
        {'skill': 'data-analysis', 'function': 'analyze', 'args': ['previous']},
    ]
    
    print(f"  Chain: {test_chain}")
    print(f"  [Simulated - skills need implementation]")
    
    # 测试 4: 便捷调用
    print("\n[Test 4] Quick API")
    print("-" * 50)
    
    print(f"  call('github', 'fetch_trending')")
    print(f"  chain([...])")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
