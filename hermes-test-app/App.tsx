/**
 * Hermes Test App
 *
 * A test application for validating the Lêtô Hermes analysis toolkit.
 * Contains intentional secrets, endpoints, and security features for testing.
 *
 * DO NOT USE IN PRODUCTION - Contains intentional vulnerabilities.
 */

import React, {useState, useEffect} from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  TextInput,
  Alert,
} from 'react-native';

// Import secrets (intentional - for testing detection)
import {
  API_KEY_INTERNAL,
  JWT_ACCESS_TOKEN,
  DEBUG_MODE,
  INTERNAL_ADMIN_PASSWORD,
  FIREBASE_CONFIG,
  AWS_ACCESS_KEY_ID,
} from './src/config/secrets';

// Import endpoints
import {ENDPOINTS, GRAPHQL_ENDPOINT} from './src/config/endpoints';

// Import API service
import {api, graphql} from './src/services/api';

type SectionProps = {
  title: string;
  children: React.ReactNode;
};

function Section({title, children}: SectionProps): React.JSX.Element {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.sectionContent}>{children}</View>
    </View>
  );
}

function App(): React.JSX.Element {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState('Ready');

  // Log some sensitive info on mount (intentional - for testing detection)
  useEffect(() => {
    if (DEBUG_MODE) {
      console.log('Debug mode enabled');
      console.log('API Key:', API_KEY_INTERNAL);
      console.log('Firebase Project:', FIREBASE_CONFIG.projectId);
      // Intentionally log sensitive data
      console.log('Admin password:', INTERNAL_ADMIN_PASSWORD);
    }
  }, []);

  const handleLogin = async () => {
    setStatus('Logging in...');
    try {
      // This will fail (no real server) but tests API call detection
      const result = await api.login(email, password);
      setStatus(`Login result: ${JSON.stringify(result)}`);
    } catch (error) {
      setStatus('Login failed (expected - no server)');
    }
  };

  const handleFetchProfile = async () => {
    setStatus('Fetching profile...');
    try {
      const result = await api.getProfile();
      setStatus(`Profile: ${JSON.stringify(result)}`);
    } catch (error) {
      setStatus('Fetch failed (expected - no server)');
    }
  };

  const handleGraphQL = async () => {
    setStatus('Testing GraphQL...');
    try {
      const result = await graphql.getUser('123');
      setStatus(`GraphQL result: ${JSON.stringify(result)}`);
    } catch (error) {
      setStatus('GraphQL failed (expected - no server)');
    }
  };

  const handleShowSecrets = () => {
    // Intentionally display secrets (for testing)
    Alert.alert(
      'Test Secrets',
      `API Key: ${API_KEY_INTERNAL.substring(0, 20)}...\n` +
        `AWS Key: ${AWS_ACCESS_KEY_ID}\n` +
        `JWT: ${JWT_ACCESS_TOKEN.substring(0, 30)}...`,
    );
  };

  const handleAdminAccess = async () => {
    setStatus('Accessing admin...');
    try {
      const result = await api.getAdminDashboard();
      setStatus(`Admin: ${JSON.stringify(result)}`);
    } catch (error) {
      setStatus('Admin access failed (expected)');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#fff" />
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.title}>Hermes Test App</Text>
          <Text style={styles.subtitle}>
            For testing Lêtô toolkit - DO NOT USE IN PRODUCTION
          </Text>
        </View>

        <Section title="Authentication">
          <TextInput
            style={styles.input}
            placeholder="Email"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
          />
          <TextInput
            style={styles.input}
            placeholder="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />
          <TouchableOpacity style={styles.button} onPress={handleLogin}>
            <Text style={styles.buttonText}>Login (REST)</Text>
          </TouchableOpacity>
        </Section>

        <Section title="API Tests">
          <TouchableOpacity style={styles.button} onPress={handleFetchProfile}>
            <Text style={styles.buttonText}>Fetch Profile</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.button} onPress={handleGraphQL}>
            <Text style={styles.buttonText}>GraphQL Query</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.button} onPress={handleAdminAccess}>
            <Text style={styles.buttonText}>Admin Dashboard</Text>
          </TouchableOpacity>
        </Section>

        <Section title="Security Tests">
          <TouchableOpacity
            style={[styles.button, styles.dangerButton]}
            onPress={handleShowSecrets}>
            <Text style={styles.buttonText}>Show Secrets (Test)</Text>
          </TouchableOpacity>
        </Section>

        <Section title="Status">
          <Text style={styles.statusText}>{status}</Text>
        </Section>

        <Section title="Endpoints">
          <Text style={styles.infoText}>REST: {ENDPOINTS.AUTH.LOGIN}</Text>
          <Text style={styles.infoText}>GraphQL: {GRAPHQL_ENDPOINT}</Text>
          <Text style={styles.infoText}>
            Debug Mode: {DEBUG_MODE ? 'ON' : 'OFF'}
          </Text>
        </Section>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: 20,
    backgroundColor: '#6200ee',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 12,
    color: '#ffcdd2',
    marginTop: 5,
  },
  section: {
    margin: 10,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 10,
    color: '#333',
  },
  sectionContent: {
    gap: 10,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 5,
    padding: 10,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#6200ee',
    padding: 12,
    borderRadius: 5,
    alignItems: 'center',
  },
  dangerButton: {
    backgroundColor: '#d32f2f',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
  },
  statusText: {
    fontSize: 14,
    color: '#666',
    fontFamily: 'monospace',
  },
  infoText: {
    fontSize: 12,
    color: '#888',
    fontFamily: 'monospace',
  },
});

export default App;
