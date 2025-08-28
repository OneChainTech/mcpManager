#!/usr/bin/env python3
"""
数据库迁移脚本：为upstreamservice表添加headers字段
"""

import sqlite3
import os

def migrate_add_headers():
    """添加headers字段到upstreamservice表"""
    db_path = "mcp_manager.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查headers字段是否已存在
        cursor.execute("PRAGMA table_info(upstreamservice)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'headers' not in columns:
            print("正在添加headers字段...")
            
            # 添加headers字段
            cursor.execute("ALTER TABLE upstreamservice ADD COLUMN headers JSON")
            
            # 为现有记录设置默认值
            cursor.execute("UPDATE upstreamservice SET headers = '{}' WHERE headers IS NULL")
            
            print("✅ headers字段添加成功")
        else:
            print("ℹ️  headers字段已存在")
        
        # 提交更改
        conn.commit()
        
        # 显示表结构
        print("\n当前表结构:")
        cursor.execute("PRAGMA table_info(upstreamservice)")
        for column in cursor.fetchall():
            print(f"  {column[1]} ({column[2]})")
        
        # 显示现有数据
        print("\n现有服务数据:")
        cursor.execute("SELECT id, name, headers FROM upstreamservice")
        for row in cursor.fetchall():
            print(f"  ID {row[0]}: {row[1]} - headers: {row[2]}")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 开始数据库迁移...")
    migrate_add_headers()
    print("✨ 迁移完成")
