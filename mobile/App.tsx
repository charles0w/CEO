import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ChatScreen } from './src/screens/ChatScreen';
import { SettingsScreen, STORAGE_KEY, DEFAULT_URL } from './src/screens/SettingsScreen';

type Screen = 'chat' | 'settings';

export default function App() {
  const [screen, setScreen] = useState<Screen>('chat');
  const [serverUrl, setServerUrl] = useState(DEFAULT_URL);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then(url => {
      if (url) setServerUrl(url);
    });
  }, []);

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      {screen === 'chat' ? (
        <ChatScreen
          serverUrl={serverUrl}
          onOpenSettings={() => setScreen('settings')}
        />
      ) : (
        <SettingsScreen
          currentUrl={serverUrl}
          onBack={() => setScreen('chat')}
          onSave={setServerUrl}
        />
      )}
    </SafeAreaProvider>
  );
}
