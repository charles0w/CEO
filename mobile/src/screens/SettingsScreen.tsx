import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, Alert, ScrollView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

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
      <LinearGradient colors={['#06130f', '#101A25', '#1B1323']} style={StyleSheet.absoluteFill} />
      <View style={styles.orbOne} />
      <View style={styles.orbTwo} />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerRow}>
          <TouchableOpacity onPress={onBack} style={styles.back} activeOpacity={0.75}>
            <Ionicons name="chevron-back" size={19} color="#D7F8D2" />
            <Text style={styles.backText}>Back</Text>
          </TouchableOpacity>
          <View style={styles.statusPill}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>Connection</Text>
          </View>
        </View>

        <View style={styles.heroCard}>
          <Text style={styles.kicker}>CEO SETTINGS</Text>
          <Text style={styles.title}>Point the cockpit at your brain.</Text>
          <Text style={styles.subtitle}>
            Use your Mac's local WebSocket for home-network testing, or a secure tunnel when you are away.
          </Text>
        </View>

        <View style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Ionicons name="radio-outline" size={18} color="#A6F3B6" />
            <Text style={styles.label}>Server URL</Text>
          </View>
          <TextInput
            style={styles.input}
            value={url}
            onChangeText={setUrl}
            placeholder={DEFAULT_URL}
            placeholderTextColor="#6C8075"
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
          <Text style={styles.hint}>
            Local network: ws://&lt;desktop-ip&gt;:8000/ws{'\n'}
            Remote tunnel: wss://xxxx.ngrok-free.app/ws
          </Text>
        </View>

        <TouchableOpacity style={styles.saveBtn} onPress={save} activeOpacity={0.84}>
          <Text style={styles.saveBtnText}>Save and connect</Text>
          <Ionicons name="arrow-forward" size={18} color="#06130f" />
        </TouchableOpacity>

        <View style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Ionicons name="compass-outline" size={18} color="#F7C66B" />
            <Text style={styles.label}>Find your Mac IP</Text>
          </View>
          <Text style={styles.hint}>
            macOS: run <Text style={styles.code}>ipconfig getifaddr en0</Text>.{'\n\n'}
            Windows: run <Text style={styles.code}>ipconfig</Text> and look for the IPv4 Address under your Wi-Fi adapter.{'\n\n'}
            Outside your network: run <Text style={styles.code}>ngrok http 8000</Text>, then paste the <Text style={styles.code}>wss://</Text> URL here.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

export { STORAGE_KEY, DEFAULT_URL };

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#06130f' },
  orbOne: {
    position: 'absolute',
    top: -80,
    right: -80,
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: '#48E0A43D',
  },
  orbTwo: {
    position: 'absolute',
    bottom: -120,
    left: -90,
    width: 270,
    height: 270,
    borderRadius: 135,
    backgroundColor: '#F4B86024',
  },
  content: { padding: 20, paddingBottom: 34 },
  headerRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 },
  back: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: '#FFFFFF10',
    borderWidth: 1,
    borderColor: '#DDFBE526',
  },
  backText: { color: '#D7F8D2', fontSize: 14, fontWeight: '800' },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: '#06130F99',
    borderWidth: 1,
    borderColor: '#DDFBE526',
  },
  statusDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#9CF7C8' },
  statusText: { color: '#DDFBE5', fontSize: 12, fontWeight: '900', letterSpacing: 1 },
  heroCard: {
    borderRadius: 30,
    padding: 22,
    backgroundColor: '#0E231DCC',
    borderWidth: 1,
    borderColor: '#DDFBE52E',
    marginBottom: 14,
  },
  kicker: { color: '#F7C66B', fontSize: 11, fontWeight: '900', letterSpacing: 2.2, marginBottom: 16 },
  title: {
    color: '#FFF8E8',
    fontSize: 31,
    lineHeight: 35,
    fontWeight: '900',
    letterSpacing: -1.2,
    fontFamily: Platform.select({ ios: 'AvenirNext-Heavy', android: 'sans-serif-condensed', default: 'serif' }),
  },
  subtitle: { color: '#B6CDBD', fontSize: 14, lineHeight: 21, marginTop: 12 },
  sectionCard: {
    borderRadius: 24,
    padding: 16,
    backgroundColor: '#FFFFFF0F',
    borderWidth: 1,
    borderColor: '#DDFBE522',
    marginTop: 12,
  },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  label: { color: '#E7F9D9', fontSize: 12, letterSpacing: 1.4, fontWeight: '900', textTransform: 'uppercase' },
  input: {
    backgroundColor: '#06130FCC',
    borderRadius: 17,
    paddingHorizontal: 14,
    paddingVertical: 13,
    color: '#FFF8E8',
    fontSize: 14,
    borderWidth: 1,
    borderColor: '#DDFBE526',
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
  },
  hint: { color: '#94A998', fontSize: 13, marginTop: 11, lineHeight: 21 },
  code: {
    color: '#D9F99D',
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
  },
  saveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#D9F99D',
    borderRadius: 22,
    paddingVertical: 16,
    marginTop: 14,
    shadowColor: '#D9F99D',
    shadowOpacity: 0.28,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 12 },
  },
  saveBtnText: { color: '#06130f', fontSize: 15, fontWeight: '900', letterSpacing: 0.5, textTransform: 'uppercase' },
});
