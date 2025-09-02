// PWA Utility Functions for HadadaHealth

class PWAUtils {
  constructor() {
    this.dbName = 'HadadaHealthDB';
    this.dbVersion = 1;
    this.db = null;
    this.initDB();
  }

  // Initialize IndexedDB for offline storage
  async initDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create object stores for offline data
        if (!db.objectStoreNames.contains('appointments')) {
          const appointmentStore = db.createObjectStore('appointments', { keyPath: 'id' });
          appointmentStore.createIndex('date', 'date', { unique: false });
          appointmentStore.createIndex('therapist_id', 'therapist_id', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('patients')) {
          const patientStore = db.createObjectStore('patients', { keyPath: 'id' });
          patientStore.createIndex('name', 'name', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('notes')) {
          const notesStore = db.createObjectStore('notes', { keyPath: 'id' });
          notesStore.createIndex('appointment_id', 'appointment_id', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('offline_actions')) {
          db.createObjectStore('offline_actions', { keyPath: 'id', autoIncrement: true });
        }
      };
    });
  }

  // Store data for offline access
  async storeOfflineData(storeName, data) {
    if (!this.db) await this.initDB();
    
    const transaction = this.db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    
    if (Array.isArray(data)) {
      data.forEach(item => store.put(item));
    } else {
      store.put(data);
    }
    
    return transaction.complete;
  }

  // Retrieve data from offline storage
  async getOfflineData(storeName, key = null) {
    if (!this.db) await this.initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      
      let request;
      if (key) {
        request = store.get(key);
      } else {
        request = store.getAll();
      }
      
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // Store action for later sync when online
  async storeOfflineAction(action) {
    if (!this.db) await this.initDB();
    
    const actionData = {
      ...action,
      timestamp: Date.now(),
      synced: false
    };
    
    const transaction = this.db.transaction(['offline_actions'], 'readwrite');
    const store = transaction.objectStore('offline_actions');
    
    return new Promise((resolve, reject) => {
      const request = store.add(actionData);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // Get pending offline actions
  async getPendingActions() {
    if (!this.db) await this.initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['offline_actions'], 'readonly');
      const store = transaction.objectStore('offline_actions');
      
      const request = store.getAll();
      request.onsuccess = () => {
        const actions = request.result.filter(action => !action.synced);
        resolve(actions);
      };
      request.onerror = () => reject(request.error);
    });
  }

  // Mark action as synced
  async markActionSynced(actionId) {
    if (!this.db) await this.initDB();
    
    const transaction = this.db.transaction(['offline_actions'], 'readwrite');
    const store = transaction.objectStore('offline_actions');
    
    return new Promise((resolve, reject) => {
      const getRequest = store.get(actionId);
      getRequest.onsuccess = () => {
        const action = getRequest.result;
        if (action) {
          action.synced = true;
          const putRequest = store.put(action);
          putRequest.onsuccess = () => resolve();
          putRequest.onerror = () => reject(putRequest.error);
        } else {
          resolve();
        }
      };
      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  // Check if online
  isOnline() {
    return navigator.onLine;
  }

  // Enhanced fetch with offline fallback
  async enhancedFetch(url, options = {}) {
    if (this.isOnline()) {
      try {
        const response = await fetch(url, options);
        
        // Cache successful GET requests
        if (options.method === 'GET' || !options.method) {
          if (response.ok) {
            const data = await response.clone().json();
            
            // Determine store based on URL
            if (url.includes('/api/appointments') || url.includes('/bookings')) {
              await this.storeOfflineData('appointments', data);
            } else if (url.includes('/api/patients')) {
              await this.storeOfflineData('patients', data);
            }
          }
        }
        
        return response;
      } catch (error) {
        return this.handleOfflineRequest(url, options);
      }
    } else {
      return this.handleOfflineRequest(url, options);
    }
  }

  // Handle requests when offline
  async handleOfflineRequest(url, options) {
    if (options.method === 'GET' || !options.method) {
      // Try to serve from cache
      if (url.includes('/api/appointments') || url.includes('/bookings')) {
        const data = await this.getOfflineData('appointments');
        return new Response(JSON.stringify(data), {
          headers: { 'Content-Type': 'application/json' }
        });
      } else if (url.includes('/api/patients')) {
        const data = await this.getOfflineData('patients');
        return new Response(JSON.stringify(data), {
          headers: { 'Content-Type': 'application/json' }
        });
      }
    } else {
      // Store POST/PUT/DELETE actions for later sync
      await this.storeOfflineAction({
        url,
        method: options.method,
        headers: options.headers,
        body: options.body
      });
      
      // Return a success response to prevent errors
      return new Response(JSON.stringify({ 
        success: true, 
        offline: true, 
        message: 'Action stored for sync when online' 
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    throw new Error('Network unavailable and no cached data');
  }

  // Sync offline actions when back online
  async syncOfflineActions() {
    if (!this.isOnline()) return;
    
    const pendingActions = await this.getPendingActions();
    
    for (const action of pendingActions) {
      try {
        const response = await fetch(action.url, {
          method: action.method,
          headers: action.headers,
          body: action.body
        });
        
        if (response.ok) {
          await this.markActionSynced(action.id);
          console.log('Synced offline action:', action.id);
        }
      } catch (error) {
        console.error('Failed to sync action:', action.id, error);
      }
    }
  }

  // Install event listeners for online/offline detection
  setupEventListeners() {
    window.addEventListener('online', () => {
      console.log('Back online - syncing offline actions');
      this.syncOfflineActions();
    });
    
    window.addEventListener('offline', () => {
      console.log('Gone offline - switching to offline mode');
    });
  }
}

// Global PWA utils instance
window.pwaUtils = new PWAUtils();
window.pwaUtils.setupEventListeners();

// Enhanced fetch function for the app to use
window.enhancedFetch = (url, options) => window.pwaUtils.enhancedFetch(url, options);