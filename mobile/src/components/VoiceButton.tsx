import React, { useEffect, useRef } from 'react';
import { TouchableOpacity, Animated, StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  onPressIn: () => void;
  onPressOut: () => void;
  isListening: boolean;
  isConnected: boolean;
}

export function VoiceButton({ onPressIn, onPressOut, isListening, isConnected }: Props) {
  const pulse = useRef(new Animated.Value(1)).current;
  const animation = useRef<Animated.CompositeAnimation | null>(null);

  useEffect(() => {
    if (isListening) {
      animation.current = Animated.loop(
        Animated.sequence([
          Animated.timing(pulse, { toValue: 1.25, duration: 500, useNativeDriver: true }),
          Animated.timing(pulse, { toValue: 1, duration: 500, useNativeDriver: true }),
        ])
      );
      animation.current.start();
    } else {
      animation.current?.stop();
      Animated.timing(pulse, { toValue: 1, duration: 150, useNativeDriver: true }).start();
    }
  }, [isListening, pulse]);

  const color = !isConnected ? '#333' : isListening ? '#ff4444' : '#4a9eff';

  return (
    <TouchableOpacity
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      disabled={!isConnected}
      activeOpacity={0.8}
    >
      <Animated.View style={[styles.button, { transform: [{ scale: pulse }], borderColor: color }]}>
        <Ionicons name={isListening ? 'stop' : 'mic'} size={22} color={color} />
      </Animated.View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#0d1a2e',
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
