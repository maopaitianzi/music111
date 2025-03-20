/**
 * 音频录制组件
 * 
 * 该组件提供音频录制功能，允许用户录制一段音频进行音乐识别。
 * 主要功能包括:
 * - 音频录制
 * - 录制时间控制
 * - 录制状态显示
 * - 波形可视化
 */

import React, { useState, useRef, useEffect } from 'react';
import './AudioRecorder.css';

// 录音状态枚举
const RecordingState = {
  INACTIVE: 'inactive',
  RECORDING: 'recording',
  PAUSED: 'paused',
  COMPLETED: 'completed'
};

// 默认录制配置
const DEFAULT_CONFIG = {
  maxDuration: 10, // 最大录制时长（秒）
  sampleRate: 44100, // 采样率
  minDuration: 3, // 最小有效录制时长（秒）
};

const AudioRecorder = ({ onRecordingComplete, config = {} }) => {
  // 合并配置
  const recordConfig = { ...DEFAULT_CONFIG, ...config };
  
  // 状态管理
  const [recordingState, setRecordingState] = useState(RecordingState.INACTIVE);
  const [duration, setDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [visualizationData, setVisualizationData] = useState([]);
  
  // Refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const analyserRef = useRef(null);
  const audioContextRef = useRef(null);
  const timerRef = useRef(null);
  
  // 初始化可视化画布
  useEffect(() => {
    if (canvasRef.current && recordingState === RecordingState.RECORDING) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      
      const renderWaveform = () => {
        if (!analyserRef.current) return;
        
        const analyser = analyserRef.current;
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        analyser.getByteTimeDomainData(dataArray);
        
        // 清除画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 设置波形样式
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#4CAF50';
        ctx.beginPath();
        
        const sliceWidth = canvas.width / bufferLength;
        let x = 0;
        
        for (let i = 0; i < bufferLength; i++) {
          const v = dataArray[i] / 128.0;
          const y = v * (canvas.height / 2);
          
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
          
          x += sliceWidth;
        }
        
        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
        
        // 保存当前可视化数据
        setVisualizationData([...dataArray]);
        
        // 持续动画
        animationRef.current = requestAnimationFrame(renderWaveform);
      };
      
      renderWaveform();
    }
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [recordingState]);
  
  // 清理资源
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [audioUrl]);
  
  // 开始录音
  const startRecording = async () => {
    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // 创建音频上下文和分析器
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 2048;
      source.connect(analyserRef.current);
      
      // 创建媒体录制器
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      // 收集录音数据
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      // 录音结束处理
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const url = URL.createObjectURL(audioBlob);
        
        setAudioBlob(audioBlob);
        setAudioUrl(url);
        setRecordingState(RecordingState.COMPLETED);
        
        // 回调函数，将录音结果传递给父组件
        if (onRecordingComplete) {
          onRecordingComplete({
            blob: audioBlob,
            url: url,
            duration: duration
          });
        }
        
        // 停止所有轨道
        stream.getTracks().forEach(track => track.stop());
      };
      
      // 启动录音
      mediaRecorderRef.current.start();
      setRecordingState(RecordingState.RECORDING);
      
      // 设置计时器
      let seconds = 0;
      timerRef.current = setInterval(() => {
        seconds++;
        setDuration(seconds);
        
        // 检查是否达到最大录制时间
        if (seconds >= recordConfig.maxDuration) {
          stopRecording();
        }
      }, 1000);
      
    } catch (error) {
      console.error('录音失败:', error);
    }
  };
  
  // 暂停录音
  const pauseRecording = () => {
    if (mediaRecorderRef.current && recordingState === RecordingState.RECORDING) {
      mediaRecorderRef.current.pause();
      clearInterval(timerRef.current);
      setRecordingState(RecordingState.PAUSED);
    }
  };
  
  // 恢复录音
  const resumeRecording = () => {
    if (mediaRecorderRef.current && recordingState === RecordingState.PAUSED) {
      mediaRecorderRef.current.resume();
      
      // 重启计时器
      timerRef.current = setInterval(() => {
        setDuration(prev => {
          const newDuration = prev + 1;
          if (newDuration >= recordConfig.maxDuration) {
            stopRecording();
          }
          return newDuration;
        });
      }, 1000);
      
      setRecordingState(RecordingState.RECORDING);
    }
  };
  
  // 停止录音
  const stopRecording = () => {
    if (mediaRecorderRef.current && (recordingState === RecordingState.RECORDING || recordingState === RecordingState.PAUSED)) {
      mediaRecorderRef.current.stop();
      clearInterval(timerRef.current);
      
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }
  };
  
  // 重置录音
  const resetRecording = () => {
    setRecordingState(RecordingState.INACTIVE);
    setDuration(0);
    setAudioBlob(null);
    
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
  };
  
  // 格式化时间显示
  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };
  
  // 渲染录音按钮
  const renderRecordButton = () => {
    switch (recordingState) {
      case RecordingState.INACTIVE:
        return (
          <button 
            className="record-button" 
            onClick={startRecording}
          >
            开始录音
          </button>
        );
        
      case RecordingState.RECORDING:
        return (
          <div className="recording-controls">
            <button 
              className="pause-button" 
              onClick={pauseRecording}
            >
              暂停
            </button>
            <button 
              className="stop-button" 
              onClick={stopRecording}
            >
              停止
            </button>
          </div>
        );
        
      case RecordingState.PAUSED:
        return (
          <div className="recording-controls">
            <button 
              className="resume-button" 
              onClick={resumeRecording}
            >
              继续
            </button>
            <button 
              className="stop-button" 
              onClick={stopRecording}
            >
              停止
            </button>
          </div>
        );
        
      case RecordingState.COMPLETED:
        return (
          <div className="recording-controls">
            <button 
              className="reset-button" 
              onClick={resetRecording}
            >
              重新录制
            </button>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <div className="audio-recorder">
      <div className="recorder-header">
        <h3>音频录制</h3>
        <div className="recorder-timer">
          {formatTime(duration)} / {formatTime(recordConfig.maxDuration)}
        </div>
      </div>
      
      <div className="recorder-visualization">
        {(recordingState === RecordingState.RECORDING || recordingState === RecordingState.PAUSED) && (
          <canvas 
            ref={canvasRef} 
            width="300" 
            height="100"
            className="waveform-canvas"
          />
        )}
        
        {recordingState === RecordingState.COMPLETED && audioUrl && (
          <div className="audio-playback">
            <audio src={audioUrl} controls />
          </div>
        )}
        
        {recordingState === RecordingState.INACTIVE && (
          <div className="recorder-placeholder">
            点击"开始录音"按钮来识别正在播放的音乐
          </div>
        )}
      </div>
      
      <div className="recorder-controls">
        {renderRecordButton()}
      </div>
      
      {recordingState === RecordingState.RECORDING && (
        <div className="recording-indicator">
          <div className="recording-icon"></div>
          正在录音...
        </div>
      )}
      
      {recordingState === RecordingState.COMPLETED && duration < recordConfig.minDuration && (
        <div className="recording-warning">
          录音时间过短，请重新录制至少 {recordConfig.minDuration} 秒
        </div>
      )}
    </div>
  );
};

export default AudioRecorder; 