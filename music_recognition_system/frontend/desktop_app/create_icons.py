from PIL import Image, ImageDraw, ImageFont
import os

def create_directory_if_not_exists(directory):
    """创建目录（如果不存在）"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def create_play_icon(output_path, size=128):
    """创建播放图标"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算三角形的点
    margin = size // 4
    points = [
        (margin, margin),
        (size - margin, size // 2),
        (margin, size - margin)
    ]
    
    # 绘制三角形
    draw.polygon(points, fill=(29, 185, 84, 255))  # 绿色 #1DB954
    
    # 保存图标
    img.save(output_path)
    print(f"已创建: {output_path}")

def create_remove_icon(output_path, size=128):
    """创建删除图标"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算X的点
    margin = size // 4
    thickness = size // 10
    
    # 绘制X
    draw.line([(margin, margin), (size - margin, size - margin)], fill=(231, 76, 60, 255), width=thickness)  # 红色 #e74c3c
    draw.line([(margin, size - margin), (size - margin, margin)], fill=(231, 76, 60, 255), width=thickness)
    
    # 保存图标
    img.save(output_path)
    print(f"已创建: {output_path}")

def create_favorite_icon(output_path, size=128):
    """创建收藏图标（心形）"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 简化的心形绘制
    # 使用两个圆和一个三角形来近似心形
    circle_radius = size // 4
    circle1_center = (size // 4, size // 3)
    circle2_center = (size - size // 4, size // 3)
    
    # 绘制两个圆
    draw.ellipse([
        circle1_center[0] - circle_radius,
        circle1_center[1] - circle_radius,
        circle1_center[0] + circle_radius,
        circle1_center[1] + circle_radius
    ], fill=(231, 76, 60, 255))  # 红色 #e74c3c
    
    draw.ellipse([
        circle2_center[0] - circle_radius,
        circle2_center[1] - circle_radius,
        circle2_center[0] + circle_radius,
        circle2_center[1] + circle_radius
    ], fill=(231, 76, 60, 255))
    
    # 绘制三角形底部
    points = [
        (size // 8, size // 3 + size // 12),
        (size - size // 8, size // 3 + size // 12),
        (size // 2, size - size // 4)
    ]
    draw.polygon(points, fill=(231, 76, 60, 255))
    
    # 保存图标
    img.save(output_path)
    print(f"已创建: {output_path}")

def create_user_avatar(output_path, size=128):
    """创建用户头像图标"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制圆形背景
    draw.ellipse([(0, 0), (size, size)], fill=(29, 185, 84, 255))  # 绿色 #1DB954
    
    # 绘制简化的用户轮廓
    # 头部
    head_radius = size // 3
    head_center = (size // 2, size // 3)
    draw.ellipse([
        head_center[0] - head_radius,
        head_center[1] - head_radius,
        head_center[0] + head_radius,
        head_center[1] + head_radius
    ], fill=(255, 255, 255, 255))
    
    # 身体
    body_width = size // 2
    body_top = head_center[1] + head_radius - size // 10
    body_bottom = size - size // 6
    draw.ellipse([
        size // 2 - body_width // 2,
        body_top,
        size // 2 + body_width // 2,
        body_bottom * 2 - body_top
    ], fill=(255, 255, 255, 255))
    
    # 保存图标
    img.save(output_path)
    print(f"已创建: {output_path}")

def main():
    # 设置图标目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(current_dir, "assets", "icons")
    create_directory_if_not_exists(icons_dir)
    
    # 创建各个图标
    create_play_icon(os.path.join(icons_dir, "play.png"))
    create_remove_icon(os.path.join(icons_dir, "remove.png"))
    create_favorite_icon(os.path.join(icons_dir, "favorite.png"))
    create_user_avatar(os.path.join(icons_dir, "user_avatar.png"))
    
    print("所有图标创建完成!")

if __name__ == "__main__":
    main() 