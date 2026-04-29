import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, Alert, ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';

const STORAGE_KEY = 'ceo_server_url';
const DEFAULT_URL = 'ws://192.168.1.100:8000/ws';

interface Props {
  onBack: () => void;
  onSave: (url: string) => void;
  currentUrl: string;
}

export function SettingsScreen({ onBack, onSave, currentUrl }: Props) {
  const [url, setUrl] = useState(currentUrl);

  const save = async () => {
    if (!url.startsWith('ws://') && !url.startsWith('wss://')) {
      Alert.alert('Invalid URL', 'Server URL must start with ws:// or wss://');
      return;
    }
    await AsyncStorage.setItem(STORAGE_KEY, url);
    onSave(url);
    onBack();
  };

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient colors={['#050510', '#0a0a1a']} style={StyleSheet.absoluteFill} />
      <ScrollView contentContainerStyle={styles.content}>
        <TouchableOpacity onPress={onBack} style={styles.back}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>

        <Text style={styles.title}>SETTINGS</Text>

        <View style={styles.section}>
          <Text style={styles.label}>CEO Server URL</Text>
          <TextInput
            style={styles.input}
            value={url}
            onChangeText={setUrl}
            placeholder={DEFAULT_URL}
            placeholderTextColor="#334"
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
          <Text style={styles.hint}>
            Local network: ws://&lt;desktop-ip&gt;:8000/ws{'\n'}
            Remote (ngrok): wss://xxxx.ngrok-free.app/ws
          </Text>
        </View>

        <TouchableOpacity style={styles.saveBtn} onPress={save}>
          <Text style={styles.saveBtnText}>SAVE & CONNECT</Text>
        </TouchableOpacity>

        <View style={styles.section}>
          <Text style={styles.label}>How to find your Desktop IP</Text>
          <Text style={styles.hint}>
            Windows: run <Text style={styles.code}>ipconfig</Text> and look for "IPv4 Address" under your WiFi adapter.{'\n\n'}
            macOS: run <Text style={styles.code}>ipconfig getifaddr en0</Text>.{'\n\n'}
            For remote access from outside your network,{'\n'}
            install ngrok and run: <Text style={styles.code}>ngrok http 8000</Text>
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

export { STORAGE_KEY, DEFAULT_URL };

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#050510' },
  content: { padding: 24 },
  back: { marginBottom: 24 },
  backText: { color: '#4a9eff', fontSize: 16 },
  title: { color: '#4a9eff', fontSize: 22, fontWeight: '700', letterSpacing: 4, marginBottom: 32 },
  section: { marginBottom: 28 },
  label: { color: '#8ab4d4', fontSize: 13, letterSpacing: 1, marginBottom: 10, textTransform: 'uppercase' },
  input: {
    backgroundColor: '#0d1a2e',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: '#e0e8f8',
    fontSize: 14,
    borderWidth: 1,
    borderColor: '#1a3a5c',
    fontFamily: 'monospace',
  },
  hint: { color: '#445566', fontSize: 12, marginTop: 10, lineHeight: 20 },
  code: { color: '#4a9eff', fontFamily: 'monospace' },
  saveBtn: {
    backgroundColor: '#0d3060',
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#4a9eff',
    marginBottom: 32,
  },
  saveBtnText: { color: '#4a9eff', fontSize: 15, fontWeight: '700', letterSpacing: 2 },
});
