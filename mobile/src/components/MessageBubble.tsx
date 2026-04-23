import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export interface Message {
  id: string;
  role: 'user' | 'ceo';
  text: string;
  timestamp: Date;
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  return (
    <View style={[styles.row, isUser ? styles.rowRight : styles.rowLeft]}>
      {!isUser && (
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>C</Text>
        </View>
      )}
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.ceoBubble]}>
        <Text style={styles.text}>{message.text}</Text>
        <Text style={styles.time}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    marginVertical: 6,
    alignItems: 'flex-end',
    paddingHorizontal: 4,
  },
  rowLeft: { justifyContent: 'flex-start' },
  rowRight: { justifyContent: 'flex-end' },
  avatar: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#0d3060',
    borderWidth: 1,
    borderColor: '#4a9eff',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
    marginBottom: 4,
  },
  avatarText: { color: '#4a9eff', fontSize: 12, fontWeight: '700' },
  bubble: {
    maxWidth: '78%',
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  userBubble: {
    backgroundColor: '#0d2a4a',
    borderBottomRightRadius: 4,
    borderWidth: 1,
    borderColor: '#1a4a7a',
  },
  ceoBubble: {
    backgroundColor: '#0a1a2e',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#4a9eff44',
  },
  text: { color: '#e0e8f8', fontSize: 15, lineHeight: 22 },
  time: { color: '#445566', fontSize: 11, marginTop: 4, textAlign: 'right' },
});
