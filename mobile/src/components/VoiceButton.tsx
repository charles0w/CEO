import React, { useEffect, useRef } from 'react';
import { TouchableOpacity, Animated, StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

interface Props {
  onPressIn: () => void;
  onPressOut: () => void;
  isListening: boolean;
  isConnected: boolean;
}

export function VoiceButton({ onPressIn, onPressOut, isListening, isConnected }: Props) {
  const pulse = useRef(new Animated.Value(0)).current;
  const animation = useRef<Animated.CompositeAnimation | null>(null);

  useEffect(() => {
    if (isListening) {
      animation.current = Animated.loop(
        Animated.sequence([
          Animated.timing(pulse, { toValue: 1, duration: 620, useNativeDriver: true }),
          Animated.timing(pulse, { toValue: 0, duration: 620, useNativeDriver: true }),
        ])
      );
      animation.current.start();
    } else {
      animation.current?.stop();
      Animated.timing(pulse, { toValue: 0, duration: 160, useNativeDriver: true }).start();
    }
  }, [isListening, pulse]);

  const ringScale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.55] });
  const ringOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.2, 0] });
  const iconColor = !isConnected ? '#6B756D' : isListening ? '#2B1307' : '#06130f';
  const gradientColors: [string, string] = isListening ? ['#FFB45E', '#F9735B'] : ['#D9F99D', '#61E4AE'];

  return (
    <TouchableOpacity
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      disabled={!isConnected}
      activeOpacity={0.82}
      style={styles.touchTarget}
    >
      <Animated.View
        pointerEvents="none"
        style={[
          styles.pulseRing,
          {
            opacity: ringOpacity,
            transform: [{ scale: ringScale }],
            borderColor: isListening ? '#FFB45E' : '#D9F99D',
          },
        ]}
      />
      <LinearGradient colors={isConnected ? gradientColors : ['#FFFFFF10', '#FFFFFF10']} style={styles.button}>
        <View style={styles.innerSheen} />
        <Ionicons name={isListening ? 'stop' : 'mic'} size={22} color={iconColor} />
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  touchTarget: {
    width: 50,
    height: 50,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pulseRing: {
    position: 'absolute',
    width: 46,
    height: 46,
    borderRadius: 23,
    borderWidth: 1.5,
  },
  button: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#FFFFFF40',
  },
  innerSheen: {
    position: 'absolute',
    top: 6,
    left: 10,
    width: 18,
    height: 8,
    borderRadius: 9,
    backgroundColor: '#FFFFFF55',
  },
});
