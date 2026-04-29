import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Platform } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

export interface Message {
  id: string;
  role: 'user' | 'ceo';
  text: string;
  timestamp: Date;
}

export function MessageBubble({ message, index = 0 }: { message: Message; index?: number }) {
  const isUser = message.role === 'user';
  const fade = useRef(new Animated.Value(0)).current;
  const lift = useRef(new Animated.Value(10)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fade, {
        toValue: 1,
        duration: 260,
        delay: Math.min(index * 18, 160),
        useNativeDriver: true,
      }),
      Animated.timing(lift, {
        toValue: 0,
        duration: 260,
        delay: Math.min(index * 18, 160),
        useNativeDriver: true,
      }),
    ]).start();
  }, [fade, index, lift]);

  return (
    <Animated.View
      style={[
        styles.row,
        isUser ? styles.rowRight : styles.rowLeft,
        { opacity: fade, transform: [{ translateY: lift }] },
      ]}
    >
      {!isUser && (
        <LinearGradient colors={['#D9F99D', '#51D6A1']} style={styles.avatar}>
          <Text style={styles.avatarText}>C</Text>
        </LinearGradient>
      )}
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.ceoBubble]}>
        {!isUser && <Text style={styles.roleLabel}>CEO</Text>}
        <Text style={[styles.text, isUser && styles.userText]}>{message.text}</Text>
        <Text style={[styles.time, isUser && styles.userTime]}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    marginVertical: 7,
    alignItems: 'flex-end',
    paddingHorizontal: 2,
  },
  rowLeft: { justifyContent: 'flex-start' },
  rowRight: { justifyContent: 'flex-end' },
  avatar: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
    marginBottom: 4,
    shadowColor: '#D9F99D',
    shadowOpacity: 0.35,
    shadowRadius: 12,
  },
  avatarText: {
    color: '#06130f',
    fontSize: 13,
    fontWeight: '900',
    fontFamily: Platform.select({ ios: 'AvenirNext-Heavy', android: 'sans-serif-condensed', default: 'serif' }),
  },
  bubble: {
    maxWidth: '80%',
    borderRadius: 22,
    paddingHorizontal: 15,
    paddingVertical: 12,
    shadowColor: '#000',
    shadowOpacity: 0.18,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 10 },
  },
  userBubble: {
    backgroundColor: '#F7C66B',
    borderBottomRightRadius: 7,
  },
  ceoBubble: {
    backgroundColor: '#FFFFFF12',
    borderBottomLeftRadius: 7,
    borderWidth: 1,
    borderColor: '#DDFBE526',
  },
  roleLabel: {
    color: '#A6F3B6',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.7,
    marginBottom: 5,
  },
  text: {
    color: '#FFF8E8',
    fontSize: 15,
    lineHeight: 22,
  },
  userText: { color: '#231B0C' },
  time: {
    color: '#96A89B',
    fontSize: 11,
    marginTop: 6,
    textAlign: 'right',
  },
  userTime: { color: '#6C4E1A' },
});
