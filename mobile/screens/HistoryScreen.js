import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl
} from 'react-native';
import { API_BASE_URL } from '../App';

export default function HistoryScreen({ navigation }) {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/submissions?limit=50`);
      const data = await response.json();
      
      if (data.submissions) {
        setSubmissions(data.submissions);
      } else {
        setSubmissions(data);
      }
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadHistory();
    setRefreshing(false);
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'alto': return '#FF3B30';
      case 'médio': return '#FF9500';
      case 'baixo': return '#34C759';
      default: return '#8E8E93';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'done': return '#34C759';
      case 'processing': return '#007AFF';
      case 'queued': return '#FF9500';
      case 'failed': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.item}
      onPress={() => {
        if (item.status === 'done' && item.result) {
          navigation.navigate('Result', { result: item.result, submission: item });
        }
      }}
    >
      <View style={styles.itemHeader}>
        <Text style={styles.url} numberOfLines={1}>
          {item.url}
        </Text>
        <View style={[
          styles.statusBadge,
          { backgroundColor: getStatusColor(item.status) }
        ]}>
          <Text style={styles.statusText}>{item.status}</Text>
        </View>
      </View>
      
      {item.result && item.result.level && (
        <View style={styles.riskBadge}>
          <Text style={[styles.riskText, { color: getLevelColor(item.result.level) }]}>
            Risco {item.result.level}
          </Text>
        </View>
      )}
      
      <Text style={styles.date}>
        {new Date(item.created_at).toLocaleString('pt-BR')}
      </Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Carregando histórico...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={submissions}
        renderItem={renderItem}
        keyExtractor={(item) => item.job_id || item.id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>Nenhuma análise encontrada</Text>
            <Text style={styles.emptySubtext}>
              Envie uma URL para análise para ver o histórico aqui
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
  },
  item: {
    backgroundColor: '#fff',
    padding: 15,
    marginHorizontal: 15,
    marginVertical: 8,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  url: {
    flex: 1,
    fontSize: 14,
    color: '#333',
    marginRight: 10,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  riskBadge: {
    marginTop: 5,
  },
  riskText: {
    fontSize: 12,
    fontWeight: '600',
  },
  date: {
    marginTop: 8,
    fontSize: 12,
    color: '#999',
  },
  empty: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
});

