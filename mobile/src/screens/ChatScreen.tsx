import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View, Text, TextInput, FlatList,
  TouchableOpacity, KeyboardAvoidingView,
  Platform, StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system/legacy';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useWebSocket, ServerMessage } from '../hooks/useWebSocket';
import { MessageBubble, Message } from '../components/MessageBubble';
import { VoiceButton } from '../components/VoiceButton';

interface Props {
  serverUrl: string;
  onOpenSettings: () => void;
}

export function ChatScreen({ serverUrl, onOpenSettings }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const flatListRef = useRef<FlatList>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);
  const { isConnected, sendMessage, lastMessage } = useWebSocket(serverUrl);

  useEffect(() => {
    (async () => {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
    })();
  }, []);

  useEffect(() => {
    if (lastMessage) handleServerMessage(lastMessage);
  }, [lastMessage]);

  const addMessage = (role: 'user' | 'ceo', text: string) => {
    setMessages(prev => [
      ...prev,
      { id: Date.now().toString(), role, text, timestamp: new Date() },
    ]);
    setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 80);
  };

  const playAudioBase64 = async (audioBase64: string) => {
    try {
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }
      const { sound } = await Audio.Sound.createAsync(
        { uri: `data:audio/mp3;base64,${audioBase64}` },
        { shouldPlay: true }
      );
      soundRef.current = sound;
    } catch (e) {
      console.warn('Audio playback error:', e);
    }
  };

  const handleServerMessage = useCallback(async (msg: ServerMessage) => {
    if (msg.type === 'transcription') {
      addMessage('user', msg.text);
    } else if (msg.type === 'response') {
      addMessage('ceo', msg.text);
      if (msg.audio) await playAudioBase64(msg.audio);
    }
  }, []);

  const sendText = () => {
    const text = inputText.trim();
    if (!text || !isConnected) return;
    addMessage('user', text);
    sendMessage({ type: 'text', content: text });
    setInputText('');
  };

  const startRecording = async () => {
    try {
      recordingRef.current = new Audio.Recording();
      await recordingRef.current.prepareToRecordAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      await recordingRef.current.startAsync();
      setIsListening(true);
    } catch (e) {
      console.warn('Record error:', e);
    }
  };

  const stopRecording = async () => {
    if (!recordingRef.current) return;
    try {
      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;
      setIsListening(false);
      if (uri) {
        const base64 = await FileSystem.readAsStringAsync(uri, {
          encoding: FileSystem.EncodingType.Base64,
        });
        sendMessage({ type: 'voice', audio: base64 });
      }
    } catch (e) {
      console.warn('Stop record error:', e);
      setIsListening(false);
    }
  };

  const resetConversation = () => {
    setMessages([]);
    sendMessage({ type: 'reset' });
  };

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient colors={['#050510', '#070718']} style={StyleSheet.absoluteFill} />

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={[styles.dot, { backgroundColor: isConnected ? '#00ff88' : '#ff4444' }]} />
          <Text style={styles.title}>CEO</Text>
          <Text style={styles.subtitle}>{isConnected ? 'online' : 'connecting...'}</Text>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity onPress={resetConversation} style={styles.iconBtn}>
            <Ionicons name="refresh-outline" size={20} color="#4a9eff88" />
          </TouchableOpacity>
          <TouchableOpacity onPress={onOpenSettings} style={styles.iconBtn}>
            <Ionicons name="settings-outline" size={20} color="#4a9eff88" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={item => item.id}
        renderItem={({ item }) => <MessageBubble message={item} />}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>
              {isConnected
                ? 'CEO is ready. Speak or type your command.'
                : 'Connecting to CEO...'}
            </Text>
          </View>
        }
      />

      {/* Input */}
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={20}
      >
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Command CEO..."
            placeholderTextColor="#334455"
            onSubmitEditing={sendText}
            returnKeyType="send"
            multiline
            editable={isConnected}
          />
          <TouchableOpacity
            onPress={sendText}
            style={styles.sendBtn}
            disabled={!isConnected || !inputText.trim()}
          >
            <Ionicons
              name="send"
              size={18}
              color={isConnected && inputText.trim() ? '#4a9eff' : '#222'}
            />
          </TouchableOpacity>
          <VoiceButton
            onPressIn={startRecording}
            onPressOut={stopRecording}
            isListening={isListening}
            isConnected={isConnected}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#050510' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#0d2040',
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerRight: { flexDirection: 'row', gap: 4 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  title: { color: '#4a9eff', fontSize: 20, fontWeight: '800', letterSpacing: 4 },
  subtitle: { color: '#334455', fontSize: 12, marginTop: 1 },
  iconBtn: { padding: 8 },
  list: { padding: 16, paddingBottom: 8 },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 80 },
  emptyText: { color: '#334455', fontSize: 14, textAlign: 'center' },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#0d2040',
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: '#0a1828',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: '#e0e8f8',
    maxHeight: 120,
    borderWidth: 1,
    borderColor: '#1a3a5c',
    fontSize: 15,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#0a1828',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#1a3a5c',
  },
});
