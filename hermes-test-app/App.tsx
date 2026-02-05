/**
 * Hermes Test App - HARDENED VERSION
 *
 * A test application for validating the Lêtô Hermes analysis toolkit.
 * Contains intentional secrets, endpoints, and security features for testing.
 *
 * This version includes:
 * - Anti-tampering checks
 * - Root/jailbreak detection
 * - Frida detection
 * - Debugger detection
 * - Obfuscated secrets
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
  SECURE_API_URL,
  DYNAMIC_TOKEN,
} from './src/config/secrets';

// Import endpoints
import {ENDPOINTS, GRAPHQL_ENDPOINT} from './src/config/endpoints';

// Import API service
import {api, graphql} from './src/services/api';

// Import anti-tampering module
import antiTamper, {
  performSecurityChecks,
  SSL_PINS,
  SecureStorage,
} from './src/security/antiTamper';

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
  const [securityStatus, setSecurityStatus] = useState<Record<string, boolean>>({});
  const [isSecure, setIsSecure] = useState(true);

  // Run security checks on mount
  useEffect(() => {
    const runSecurityChecks = () => {
      console.log('[App] Running security checks...');
      const {passed, details} = performSecurityChecks();
      setSecurityStatus(details);
      setIsSecure(passed);

      if (!passed) {
        console.warn('[App] Security check failed:', details);
        // In a real app, this might prevent usage
        // For testing, we just log and continue
      }

      // Additional Frida-specific detection
      try {
        // Check for Frida's Java.perform override
        const originalPerform = (global as any).Java?.perform;
        if (originalPerform && originalPerform.toString().includes('native')) {
          console.warn('[App] Possible Frida Java.perform detected');
        }
      } catch (e) {
        // Detection check failed, might be hooked
      }
    };

    runSecurityChecks();

    // Periodic security checks (can be bypassed by hooking setInterval)
    const interval = setInterval(runSecurityChecks, 30000);

    return () => clearInterval(interval);
  }, []);

  // Log some sensitive info on mount (intentional - for testing detection)
  useEffect(() => {
    if (DEBUG_MODE) {
      console.log('Debug mode enabled');
      console.log('API Key:', API_KEY_INTERNAL);
      console.log('Firebase Project:', FIREBASE_CONFIG.projectId);
      // Intentionally log sensitive data
      console.log('Admin password:', INTERNAL_ADMIN_PASSWORD);
      console.log('Secure URL:', SECURE_API_URL);
      console.log('Dynamic Token:', DYNAMIC_TOKEN);
    }
  }, []);

  const handleLogin = async () => {
    // Check security before allowing sensitive operations
    if (!isSecure && !DEBUG_MODE) {
      Alert.alert('Security Error', 'Security checks failed. Operation blocked.');
      return;
    }

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
    // Uses SecureStorage to demonstrate "encrypted" retrieval
    const storedKey = SecureStorage.getApiKey();

    Alert.alert(
      'Test Secrets (Hardened)',
      `API Key: ${API_KEY_INTERNAL.substring(0, 20)}...\n` +
        `AWS Key: ${AWS_ACCESS_KEY_ID}\n` +
        `JWT: ${JWT_ACCESS_TOKEN.substring(0, 30)}...\n` +
        `Stored Key: ${storedKey.substring(0, 10)}...\n` +
        `SSL Pins: ${Object.keys(SSL_PINS).length} domains`,
    );
  };

  const handleAdminAccess = async () => {
    // Additional integrity check before admin access
    const integrityOk = antiTamper.checkIntegrity();
    if (!integrityOk) {
      setStatus('Integrity check failed - access denied');
      return;
    }

    setStatus('Accessing admin...');
    try {
      const result = await api.getAdminDashboard();
      setStatus(`Admin: ${JSON.stringify(result)}`);
    } catch (error) {
      setStatus('Admin access failed (expected)');
    }
  };

  const handleSecurityCheck = () => {
    const {passed, details} = performSecurityChecks();
    Alert.alert(
      'Security Status',
      Object.entries(details)
        .map(([k, v]) => `${k}: ${v ? '✓' : '✗'}`)
        .join('\n') +
        `\n\nOverall: ${passed ? 'PASSED' : 'FAILED'}`,
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#fff" />
      <ScrollView style={styles.scrollView}>
        <View style={[styles.header, !isSecure && styles.headerInsecure]}>
          <Text style={styles.title}>Hermes Test App</Text>
          <Text style={styles.subtitle}>
            HARDENED - For testing Lêtô toolkit
          </Text>
          {!isSecure && (
            <Text style={styles.warningText}>⚠️ Security checks failed</Text>
          )}
        </View>

        <Section title="Security Status">
          <View style={styles.securityGrid}>
            {Object.entries(securityStatus).map(([key, value]) => (
              <View key={key} style={styles.securityItem}>
                <Text style={[styles.securityIcon, value ? styles.pass : styles.fail]}>
                  {value ? '✓' : '✗'}
                </Text>
                <Text style={styles.securityLabel}>{key}</Text>
              </View>
            ))}
          </View>
          <TouchableOpacity style={styles.button} onPress={handleSecurityCheck}>
            <Text style={styles.buttonText}>Run Security Check</Text>
          </TouchableOpacity>
        </Section>

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
          <Text style={styles.infoText}>Secure: {SECURE_API_URL}</Text>
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
  headerInsecure: {
    backgroundColor: '#d32f2f',
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
  warningText: {
    fontSize: 14,
    color: '#ffeb3b',
    marginTop: 10,
    fontWeight: 'bold',
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
  securityGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 10,
  },
  securityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    backgroundColor: '#f5f5f5',
    borderRadius: 5,
  },
  securityIcon: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  securityLabel: {
    fontSize: 12,
    color: '#666',
  },
  pass: {
    color: '#4caf50',
  },
  fail: {
    color: '#f44336',
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
