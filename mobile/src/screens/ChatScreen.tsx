import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  View, Text, TextInput, FlatList,
  TouchableOpacity, KeyboardAvoidingView,
  Platform, StyleSheet, Animated, Easing,
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
  const heroFade = useRef(new Animated.Value(0)).current;
  const heroLift = useRef(new Animated.Value(18)).current;
  const haloSpin = useRef(new Animated.Value(0)).current;
  const { isConnected, sendMessage, lastMessage } = useWebSocket(serverUrl);

  const sessionStats = useMemo(() => {
    const userTurns = messages.filter(message => message.role === 'user').length;
    const ceoTurns = messages.length - userTurns;
    const host = serverUrl.replace(/^wss?:\/\//, '').replace(/\/ws$/, '');

    return {
      totalTurns: messages.length,
      userTurns,
      ceoTurns,
      host,
    };
  }, [messages, serverUrl]);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(heroFade, {
        toValue: 1,
        duration: 520,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(heroLift, {
        toValue: 0,
        duration: 520,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
    ]).start();

    const spinAnimation = Animated.loop(
      Animated.timing(haloSpin, {
        toValue: 1,
        duration: 14000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    );
    spinAnimation.start();

    return () => spinAnimation.stop();
  }, [haloSpin, heroFade, heroLift]);

  useEffect(() => {
    (async () => {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
    })();
  }, []);

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

  useEffect(() => {
    if (lastMessage) handleServerMessage(lastMessage);
  }, [lastMessage, handleServerMessage]);

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

  const haloRotate = haloSpin.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const renderDashboard = () => (
    <Animated.View
      style={[
        styles.dashboard,
        { opacity: heroFade, transform: [{ translateY: heroLift }] },
      ]}
    >
      <View style={styles.heroCard}>
        <Animated.View style={[styles.heroHalo, { transform: [{ rotate: haloRotate }] }]} />
        <View style={styles.heroTopline}>
          <View style={styles.pill}>
            <View style={[styles.pillDot, isConnected ? styles.dotOnline : styles.dotOffline]} />
            <Text style={styles.pillText}>{isConnected ? 'Live link' : 'Reconnecting'}</Text>
          </View>
          <Text style={styles.heroKicker}>LOCAL COMMAND CENTER</Text>
        </View>
        <Text style={styles.heroTitle}>Ask, delegate, build.</Text>
        <Text style={styles.heroBody}>
          CEO is tuned for local-first work: voice, chat, code assistance, and fast handoffs from one clean cockpit.
        </Text>
      </View>

      <View style={styles.metricGrid}>
        <MetricCard label="Turns" value={String(sessionStats.totalTurns)} detail={`${sessionStats.userTurns} you / ${sessionStats.ceoTurns} CEO`} />
        <MetricCard label="Runtime" value={isConnected ? 'Online' : 'Offline'} detail={sessionStats.host} accent={isConnected ? '#9CF7C8' : '#FF8E8E'} />
        <MetricCard label="Voice" value={isListening ? 'Listening' : 'Ready'} detail="hold mic to talk" accent={isListening ? '#FFB45E' : '#8EEBFF'} />
      </View>
    </Animated.View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient colors={['#06130f', '#0b1821', '#160f1f']} style={StyleSheet.absoluteFill} />
      <View style={styles.orbOne} />
      <View style={styles.orbTwo} />
      <View style={styles.gridWash} />

      <View style={styles.header}>
        <View style={styles.brandBlock}>
          <Text style={styles.eyebrow}>CEO</Text>
          <Text style={styles.title}>Personal AI Ops</Text>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity onPress={resetConversation} style={styles.iconBtn} activeOpacity={0.75}>
            <Ionicons name="refresh-outline" size={19} color="#D7F8D2" />
          </TouchableOpacity>
          <TouchableOpacity onPress={onOpenSettings} style={styles.iconBtn} activeOpacity={0.75}>
            <Ionicons name="settings-outline" size={19} color="#D7F8D2" />
          </TouchableOpacity>
        </View>
      </View>

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={item => item.id}
        renderItem={({ item, index }) => <MessageBubble message={item} index={index} />}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={renderDashboard}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyTitle}>{isConnected ? 'Ready for the first move.' : 'Finding the backend...'}</Text>
            <Text style={styles.emptyText}>
              {isConnected
                ? 'Try: summarize my plan, draft a next action, or ask CEO to reason through a build step.'
                : 'Start the FastAPI server on port 8000, then keep this screen open.'}
            </Text>
            <View style={styles.promptRail}>
              <Text style={styles.promptChip}>Plan</Text>
              <Text style={styles.promptChip}>Research</Text>
              <Text style={styles.promptChip}>Code</Text>
            </View>
          </View>
        }
      />

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={20}
      >
        <View style={styles.composerWrap}>
          <View style={styles.composerStatus}>
            <Ionicons name="sparkles-outline" size={14} color="#A6F3B6" />
            <Text style={styles.composerStatusText}>{isConnected ? 'CEO is listening' : 'Waiting for server'}</Text>
          </View>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={inputText}
              onChangeText={setInputText}
              placeholder="Give CEO a mission..."
              placeholderTextColor="#6C8075"
              onSubmitEditing={sendText}
              returnKeyType="send"
              multiline
              editable={isConnected}
            />
            <TouchableOpacity
              onPress={sendText}
              style={[styles.sendBtn, (!isConnected || !inputText.trim()) && styles.sendBtnDisabled]}
              disabled={!isConnected || !inputText.trim()}
              activeOpacity={0.8}
            >
              <Ionicons
                name="arrow-up"
                size={20}
                color={isConnected && inputText.trim() ? '#06130f' : '#6B756D'}
              />
            </TouchableOpacity>
            <VoiceButton
              onPressIn={startRecording}
              onPressOut={stopRecording}
              isListening={isListening}
              isConnected={isConnected}
            />
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function MetricCard({
  label,
  value,
  detail,
  accent = '#D9F99D',
}: {
  label: string;
  value: string;
  detail: string;
  accent?: string;
}) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={[styles.metricValue, { color: accent }]} numberOfLines={1}>{value}</Text>
      <Text style={styles.metricDetail} numberOfLines={1}>{detail}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#06130f' },
  orbOne: {
    position: 'absolute',
    top: -90,
    right: -70,
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: '#48E0A455',
  },
  orbTwo: {
    position: 'absolute',
    top: 180,
    left: -120,
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: '#F4B86022',
  },
  gridWash: {
    position: 'absolute',
    left: 18,
    right: 18,
    top: 115,
    height: 1,
    backgroundColor: '#DDFBE522',
    shadowColor: '#DDFBE5',
    shadowOpacity: 0.38,
    shadowRadius: 34,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 12,
  },
  brandBlock: { gap: 2 },
  eyebrow: {
    color: '#A6F3B6',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 4,
    fontFamily: Platform.select({ ios: 'AvenirNext-Heavy', android: 'sans-serif-condensed', default: 'serif' }),
  },
  title: {
    color: '#F4F1DE',
    fontSize: 24,
    fontWeight: '800',
    letterSpacing: -0.8,
    fontFamily: Platform.select({ ios: 'AvenirNext-DemiBold', android: 'sans-serif-medium', default: 'serif' }),
  },
  headerRight: { flexDirection: 'row', gap: 8 },
  iconBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF10',
    borderWidth: 1,
    borderColor: '#DDFBE526',
  },
  list: { paddingHorizontal: 16, paddingBottom: 8 },
  dashboard: { paddingBottom: 10 },
  heroCard: {
    overflow: 'hidden',
    minHeight: 190,
    borderRadius: 30,
    padding: 20,
    backgroundColor: '#0E231DCC',
    borderWidth: 1,
    borderColor: '#DDFBE52E',
    shadowColor: '#000',
    shadowOpacity: 0.28,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 16 },
  },
  heroHalo: {
    position: 'absolute',
    right: -60,
    top: -70,
    width: 180,
    height: 180,
    borderRadius: 90,
    borderWidth: 28,
    borderColor: '#F7C66B33',
  },
  heroTopline: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 11,
    paddingVertical: 7,
    borderRadius: 999,
    backgroundColor: '#06130F88',
    borderWidth: 1,
    borderColor: '#DDFBE52A',
  },
  pillDot: { width: 7, height: 7, borderRadius: 4 },
  dotOnline: { backgroundColor: '#9CF7C8' },
  dotOffline: { backgroundColor: '#FF8E8E' },
  pillText: { color: '#DDFBE5', fontSize: 12, fontWeight: '800' },
  heroKicker: { color: '#F7C66B', fontSize: 10, fontWeight: '900', letterSpacing: 2 },
  heroTitle: {
    color: '#FFF8E8',
    fontSize: 34,
    lineHeight: 38,
    fontWeight: '900',
    letterSpacing: -1.4,
    maxWidth: 250,
    fontFamily: Platform.select({ ios: 'AvenirNext-Heavy', android: 'sans-serif-condensed', default: 'serif' }),
  },
  heroBody: {
    color: '#B6CDBD',
    fontSize: 14,
    lineHeight: 21,
    marginTop: 12,
    maxWidth: 310,
  },
  metricGrid: { flexDirection: 'row', gap: 10, marginTop: 12 },
  metricCard: {
    flex: 1,
    minHeight: 86,
    borderRadius: 22,
    padding: 12,
    backgroundColor: '#FFFFFF0E',
    borderWidth: 1,
    borderColor: '#DDFBE520',
  },
  metricLabel: { color: '#829989', fontSize: 10, fontWeight: '900', letterSpacing: 1.5, textTransform: 'uppercase' },
  metricValue: { marginTop: 8, fontSize: 18, fontWeight: '900' },
  metricDetail: { color: '#95A89A', fontSize: 11, marginTop: 4 },
  empty: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingTop: 34,
    paddingBottom: 42,
  },
  emptyTitle: {
    color: '#FFF8E8',
    fontSize: 19,
    fontWeight: '900',
    textAlign: 'center',
    fontFamily: Platform.select({ ios: 'AvenirNext-DemiBold', android: 'sans-serif-medium', default: 'serif' }),
  },
  emptyText: { color: '#90A797', fontSize: 14, lineHeight: 21, textAlign: 'center', marginTop: 10 },
  promptRail: { flexDirection: 'row', gap: 8, marginTop: 18 },
  promptChip: {
    color: '#C9EFCF',
    fontSize: 12,
    fontWeight: '800',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: '#DDFBE512',
    borderWidth: 1,
    borderColor: '#DDFBE522',
  },
  composerWrap: {
    marginHorizontal: 12,
    marginTop: 8,
    marginBottom: 10,
    padding: 8,
    borderRadius: 28,
    backgroundColor: '#06130FE6',
    borderWidth: 1,
    borderColor: '#DDFBE52A',
  },
  composerStatus: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingBottom: 6 },
  composerStatusText: { color: '#8DA494', fontSize: 11, fontWeight: '800', letterSpacing: 0.8, textTransform: 'uppercase' },
  inputRow: { flexDirection: 'row', alignItems: 'flex-end', gap: 8 },
  input: {
    flex: 1,
    minHeight: 48,
    maxHeight: 118,
    borderRadius: 21,
    paddingHorizontal: 15,
    paddingTop: 13,
    paddingBottom: 11,
    color: '#FFF8E8',
    backgroundColor: '#FFFFFF0D',
    borderWidth: 1,
    borderColor: '#DDFBE51F',
    fontSize: 15,
    lineHeight: 20,
  },
  sendBtn: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#D9F99D',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#D9F99D',
    shadowOpacity: 0.35,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 8 },
  },
  sendBtnDisabled: {
    backgroundColor: '#FFFFFF10',
    shadowOpacity: 0,
  },
});
