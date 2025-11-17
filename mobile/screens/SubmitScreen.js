import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  ScrollView
} from 'react-native';
import { API_BASE_URL } from '../App';

export default function SubmitScreen({ navigation }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);

  const submit = async () => {
    if (!url.trim()) {
      Alert.alert('Erro', 'Por favor, insira uma URL');
      return;
    }

    // Validar formato básico de URL
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      Alert.alert('Erro', 'URL deve começar com http:// ou https://');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, user_id: null }),
      });

      if (!response.ok) {
        throw new Error('Erro ao enviar URL');
      }

      const data = await response.json();
      setJobId(data.job_id);
      
      // Polling para verificar resultado
      pollResult(data.job_id);
    } catch (error) {
      Alert.alert('Erro', `Não foi possível analisar a URL: ${error.message}`);
      setLoading(false);
    }
  };

  const pollResult = async (jobId) => {
    const maxAttempts = 30; // 30 tentativas
    let attempts = 0;

    const checkResult = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/submission/${jobId}`);
        const data = await response.json();

        if (data.status === 'done') {
          setLoading(false);
          navigation.navigate('Result', { result: data.result, submission: data });
          return;
        } else if (data.status === 'failed') {
          setLoading(false);
          Alert.alert('Erro', 'A análise falhou. Tente novamente.');
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkResult, 2000); // Verificar a cada 2 segundos
        } else {
          setLoading(false);
          Alert.alert('Timeout', 'A análise está demorando mais que o esperado.');
        }
      } catch (error) {
        setLoading(false);
        Alert.alert('Erro', 'Erro ao verificar resultado');
      }
    };

    checkResult();
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Analisar Link Suspeito</Text>
        <Text style={styles.subtitle}>
          Cole o link que você recebeu e descubra se é um golpe
        </Text>

        <TextInput
          style={styles.input}
          placeholder="https://exemplo.com"
          value={url}
          onChangeText={setUrl}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          editable={!loading}
        />

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={submit}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Analisar</Text>
          )}
        </TouchableOpacity>

        {jobId && (
          <Text style={styles.jobId}>ID da análise: {jobId.substring(0, 8)}...</Text>
        )}

        <TouchableOpacity
          style={styles.historyButton}
          onPress={() => navigation.navigate('History')}
        >
          <Text style={styles.historyButtonText}>📜 Ver Histórico</Text>
        </TouchableOpacity>
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
    paddingTop: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 30,
    lineHeight: 22,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  jobId: {
    marginTop: 15,
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
  },
  historyButton: {
    marginTop: 20,
    padding: 12,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    alignItems: 'center',
  },
  historyButtonText: {
    fontSize: 16,
    color: '#333',
  },
});

