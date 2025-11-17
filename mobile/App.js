import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';

import SubmitScreen from './screens/SubmitScreen';
import ResultScreen from './screens/ResultScreen';
import TrainingScreen from './screens/TrainingScreen';
import HistoryScreen from './screens/HistoryScreen';

const Stack = createNativeStackNavigator();

const API_BASE_URL = 'http://localhost:8000'; // Altere para seu IP em desenvolvimento

export { API_BASE_URL };

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="auto" />
      <Stack.Navigator initialRouteName="Submit">
        <Stack.Screen 
          name="Submit" 
          component={SubmitScreen}
          options={{ title: 'Analisar Link' }}
        />
        <Stack.Screen 
          name="Result" 
          component={ResultScreen}
          options={{ title: 'Resultado da Análise' }}
        />
        <Stack.Screen 
          name="Training" 
          component={TrainingScreen}
          options={{ title: 'Treinamento' }}
        />
        <Stack.Screen 
          name="History" 
          component={HistoryScreen}
          options={{ title: 'Histórico' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

