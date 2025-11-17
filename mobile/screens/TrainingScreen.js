import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert
} from 'react-native';

export default function TrainingScreen({ route }) {
  const { result } = route.params;
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(false);

  // Gerar perguntas baseadas nos checks detectados
  const questions = result.checks
    .filter(check => !check.ok)
    .slice(0, 3)
    .map((check, index) => ({
      id: index,
      question: `Qual sinal de golpe foi detectado relacionado a "${check.name.replace('_', ' ')}"?`,
      correctAnswer: check.reason,
      options: [
        check.reason,
        'O site é totalmente seguro',
        'O site usa HTTPS válido',
        'Nenhum problema foi encontrado'
      ]
    }));

  const handleAnswer = (selectedOption) => {
    if (answered) return;

    const question = questions[currentQuestion];
    const isCorrect = selectedOption === question.correctAnswer;

    if (isCorrect) {
      setScore(score + 1);
      Alert.alert('✅ Correto!', 'Você identificou o sinal corretamente.');
    } else {
      Alert.alert('❌ Incorreto', `A resposta correta é: ${question.correctAnswer}`);
    }

    setAnswered(true);
  };

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
      setAnswered(false);
    } else {
      showResults();
    }
  };

  const showResults = () => {
    const percentage = Math.round((score / questions.length) * 100);
    Alert.alert(
      'Quiz Concluído!',
      `Você acertou ${score} de ${questions.length} perguntas (${percentage}%)\n\n` +
      'Continue aprendendo sobre segurança online!',
      [{ text: 'OK' }]
    );
  };

  if (questions.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.noQuestions}>
          Não há perguntas disponíveis para este caso.
        </Text>
      </View>
    );
  }

  const question = questions[currentQuestion];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.progress}>
          Pergunta {currentQuestion + 1} de {questions.length}
        </Text>

        <View style={styles.questionCard}>
          <Text style={styles.questionText}>{question.question}</Text>

          {question.options.map((option, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.option,
                answered && option === question.correctAnswer && styles.correctOption,
                answered && option !== question.correctAnswer && styles.incorrectOption
              ]}
              onPress={() => handleAnswer(option)}
              disabled={answered}
            >
              <Text style={styles.optionText}>{option}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {answered && (
          <TouchableOpacity style={styles.nextButton} onPress={nextQuestion}>
            <Text style={styles.nextButtonText}>
              {currentQuestion < questions.length - 1 ? 'Próxima Pergunta' : 'Ver Resultados'}
            </Text>
          </TouchableOpacity>
        )}

        <View style={styles.lessonCard}>
          <Text style={styles.lessonTitle}>📚 Lição Aprendida</Text>
          <Text style={styles.lessonText}>
            {result.tips.join('\n\n')}
          </Text>
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
  progress: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
    textAlign: 'center',
  },
  questionCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
  },
  questionText: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 20,
    color: '#333',
  },
  option: {
    backgroundColor: '#f5f5f5',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  correctOption: {
    backgroundColor: '#E8F5E9',
    borderColor: '#4CAF50',
  },
  incorrectOption: {
    backgroundColor: '#FFEBEE',
    borderColor: '#F44336',
  },
  optionText: {
    fontSize: 15,
    color: '#333',
  },
  nextButton: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 20,
  },
  nextButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  lessonCard: {
    backgroundColor: '#E3F2FD',
    padding: 20,
    borderRadius: 12,
    marginTop: 10,
  },
  lessonTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 10,
    color: '#1976D2',
  },
  lessonText: {
    fontSize: 15,
    color: '#1976D2',
    lineHeight: 22,
  },
  noQuestions: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 50,
  },
});

