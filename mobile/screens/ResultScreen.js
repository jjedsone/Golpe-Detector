import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator
} from 'react-native';
import { API_BASE_URL } from '../App';

export default function ResultScreen({ route, navigation }) {
  const { result, submission } = route.params;
  const [trainingCases, setTrainingCases] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTrainingCases();
  }, []);

  const loadTrainingCases = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/training`);
      const data = await response.json();
      setTrainingCases(data);
    } catch (error) {
      console.error('Erro ao carregar casos de treino:', error);
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'alto':
        return '#FF3B30';
      case 'médio':
        return '#FF9500';
      case 'baixo':
        return '#34C759';
      default:
        return '#8E8E93';
    }
  };

  const getLevelEmoji = (level) => {
    switch (level) {
      case 'alto':
        return '🔴';
      case 'médio':
        return '🟠';
      case 'baixo':
        return '🟢';
      default:
        return '⚪';
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Badge de Nível de Risco */}
        <View style={[styles.levelBadge, { backgroundColor: getLevelColor(result.level) }]}>
          <Text style={styles.levelEmoji}>{getLevelEmoji(result.level)}</Text>
          <Text style={styles.levelText}>
            Risco {result.level.toUpperCase()}
          </Text>
        </View>

        {/* URL Analisada */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>URL Analisada</Text>
          <Text style={styles.urlText}>{result.url}</Text>
        </View>

        {/* Motivos */}
        {result.checks && result.checks.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Sinais Detectados</Text>
            {result.checks.map((check, index) => (
              <View key={index} style={styles.checkItem}>
                <Text style={styles.checkName}>• {check.name.replace('_', ' ')}</Text>
                <Text style={styles.checkReason}>{check.reason}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Dicas Pedagógicas */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Dicas de Segurança</Text>
          {result.tips.map((tip, index) => (
            <View key={index} style={styles.tipItem}>
              <Text style={styles.tipText}>{tip}</Text>
            </View>
          ))}
        </View>

        {/* Botão de Treinamento */}
        {result.level !== 'baixo' && (
          <TouchableOpacity
            style={styles.trainingButton}
            onPress={() => navigation.navigate('Training', { result })}
          >
            <Text style={styles.trainingButtonText}>
              🎓 Treinar com Este Golpe
            </Text>
          </TouchableOpacity>
        )}

        {/* Score (opcional, para debug) */}
        <View style={styles.scoreContainer}>
          <Text style={styles.scoreText}>Score: {result.score}/100</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    padding: 20,
  },
  levelBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
  },
  levelEmoji: {
    fontSize: 32,
    marginRight: 10,
  },
  levelText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  section: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 10,
    color: '#333',
  },
  urlText: {
    fontSize: 14,
    color: '#007AFF',
    fontFamily: 'monospace',
  },
  checkItem: {
    marginBottom: 10,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  checkName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
  },
  checkReason: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  tipItem: {
    backgroundColor: '#E3F2FD',
    padding: 12,
    borderRadius: 8,
    marginBottom: 10,
  },
  tipText: {
    fontSize: 15,
    color: '#1976D2',
    lineHeight: 22,
  },
  trainingButton: {
    backgroundColor: '#34C759',
    padding: 18,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
    marginBottom: 20,
  },
  trainingButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  scoreContainer: {
    alignItems: 'center',
    marginTop: 10,
  },
  scoreText: {
    fontSize: 12,
    color: '#999',
  },
});

