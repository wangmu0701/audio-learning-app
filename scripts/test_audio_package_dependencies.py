#!/usr/bin/env python3

import sys

def test_pydub():
    """测试 pydub 是否安装"""
    try:
        from pydub import AudioSegment
        print("✅ pydub 安装成功")
        return True
    except ImportError as e:
        print(f"❌ pydub 安装失败: {e}")
        return False

def test_ffmpeg():
    """测试 ffmpeg 是否可用"""
    try:
        from pydub import AudioSegment
        from pydub.utils import which
        
        ffmpeg_path = which("ffmpeg")
        if ffmpeg_path:
            print(f"✅ ffmpeg 找到了: {ffmpeg_path}")
            return True
        else:
            print("❌ ffmpeg 未找到,请确保已安装并添加到 PATH")
            return False
    except Exception as e:
        print(f"❌ ffmpeg 检查失败: {e}")
        return False

def test_audio_merge():
    """测试实际合并音频功能"""
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine
        
        # 生成两个简单的测试音频(440Hz, 1秒)
        audio1 = Sine(440).to_audio_segment(duration=1000)
        audio2 = Sine(880).to_audio_segment(duration=1000)
        
        # 合并
        combined = audio1 + audio2
        
        # 验证时长
        expected_duration = 2000  # 2秒
        if abs(len(combined) - expected_duration) < 10:
            print(f"✅ 音频合并测试成功 (时长: {len(combined)}ms)")
            return True
        else:
            print(f"❌ 音频合并测试失败 (预期: {expected_duration}ms, 实际: {len(combined)}ms)")
            return False
    except Exception as e:
        print(f"❌ 音频合并测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("Audio Package 依赖检查")
    print("=" * 60)
    
    results = []
    results.append(("pydub", test_pydub()))
    results.append(("ffmpeg", test_ffmpeg()))
    results.append(("音频合并", test_audio_merge()))
    
    print("\n" + "=" * 60)
    print("检查结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有依赖检查通过!可以开始实现 AudioPackageStage 了。")
        return 0
    else:
        print("\n⚠️  部分依赖检查失败,请先解决上述问题。")
        return 1

if __name__ == '__main__':
    sys.exit(main())