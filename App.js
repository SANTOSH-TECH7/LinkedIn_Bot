<<<<<<< HEAD
import React, { useState } from 'react';
import './App.css';
import { AlertCircle, CheckCircle, Linkedin, Send } from 'lucide-react';

function App() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    keyword: 'HR Manager',
    numPages: 10,
    maxRequests: 50,
    message: "Hi {name}, I'm exploring opportunities and would love to connect with professionals in your field. Looking forward to learning from your insights!"
  });
  
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus('running');
    setLogs(prevLogs => [...prevLogs, 'Starting LinkedIn Connector Bot...']);
    
    try {
      // In production this would call your backend
      const response = await fetch('http://localhost:5000/run-bot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      if (response.ok) {
        const result = await response.json();
        setLogs(prevLogs => [...prevLogs, `Successfully sent ${result.connectionsSent} connection requests!`]);
        if (result.output) {
          const outputLines = result.output.split('\n').filter(line => line.trim());
          setLogs(prevLogs => [...prevLogs, ...outputLines]);
        }
        setStatus('completed');
      } else {
        const error = await response.json();
        setLogs(prevLogs => [...prevLogs, `Error: ${error.message || 'Unknown error'}`]);
        setStatus('error');
      }
    } catch (error) {
      setLogs(prevLogs => [...prevLogs, `Error: ${error.message || 'Network or server error'}`]);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md overflow-hidden">
        <div className="bg-blue-600 p-6 flex items-center">
          <Linkedin className="text-white mr-3" size={32} />
          <h1 className="text-2xl font-bold text-white">LinkedIn Connection Bot</h1>
        </div>
        
        <div className="p-6">
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="col-span-2 md:col-span-1">
                <label className="block text-gray-700 font-medium mb-2">
                  LinkedIn Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="your.email@example.com"
                  required
                />
              </div>
              
              <div className="col-span-2 md:col-span-1">
                <label className="block text-gray-700 font-medium mb-2">
                  LinkedIn Password
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Your password"
                  required
                />
              </div>
              
              <div className="col-span-2">
                <label className="block text-gray-700 font-medium mb-2">
                  Search Keyword
                </label>
                <input
                  type="text"
                  name="keyword"
                  value={formData.keyword}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. HR Manager, Software Developer, Marketing Manager"
                  required
                />
              </div>
              
              <div className="col-span-1">
                <label className="block text-gray-700 font-medium mb-2">
                  Pages to Search
                </label>
                <input
                  type="number"
                  name="numPages"
                  value={formData.numPages}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="50"
                />
              </div>
              
              <div className="col-span-1">
                <label className="block text-gray-700 font-medium mb-2">
                  Max Connection Requests
                </label>
                <input
                  type="number"
                  name="maxRequests"
                  value={formData.maxRequests}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="80"
                />
              </div>
              
              <div className="col-span-2">
                <label className="block text-gray-700 font-medium mb-2">
                  Connection Message
                </label>
                <textarea
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Add a personalized message (use {name} to include the person's first name)"
                ></textarea>
              </div>
              
              <div className="col-span-2">
                <button
                  type="submit"
                  className={`w-full bg-blue-600 text-white py-3 rounded-md flex items-center justify-center ${loading ? 'opacity-70 cursor-not-allowed' : 'hover:bg-blue-700'}`}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Running Bot...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2" size={18} />
                      Start Sending Connections
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
          
          {status && (
            <div className={`mt-6 p-4 rounded-md ${
              status === 'running' ? 'bg-blue-50 border border-blue-200' :
              status === 'completed' ? 'bg-green-50 border border-green-200' : 
              'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center">
                {status === 'running' && <AlertCircle className="text-blue-500 mr-2" size={20} />}
                {status === 'completed' && <CheckCircle className="text-green-500 mr-2" size={20} />}
                {status === 'error' && <AlertCircle className="text-red-500 mr-2" size={20} />}
                <p className={`font-medium ${
                  status === 'running' ? 'text-blue-700' :
                  status === 'completed' ? 'text-green-700' : 
                  'text-red-700'
                }`}>
                  {status === 'running' ? 'Bot is running...' :
                   status === 'completed' ? 'Bot completed successfully!' : 
                   'An error occurred'}
                </p>
              </div>
            </div>
          )}
          
          {logs.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-700 mb-2">Activity Log</h3>
              <div className="bg-gray-800 text-gray-100 p-4 rounded-md h-64 overflow-y-auto">
                {logs.map((log, index) => (
                  <div key={index} className="mb-1">
                    <span className="text-gray-400">[{new Date().toLocaleTimeString()}]</span> {log}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            Note: This application automates LinkedIn connections. Please use responsibly and in accordance with LinkedIn's terms of service.
          </p>
        </div>
      </div>
    </div>
  );
}

=======
import React, { useState } from 'react';
import './App.css';
import { AlertCircle, CheckCircle, Linkedin, Send } from 'lucide-react';

function App() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    keyword: 'HR Manager',
    numPages: 10,
    maxRequests: 50,
    message: "Hi {name}, I'm exploring opportunities and would love to connect with professionals in your field. Looking forward to learning from your insights!"
  });
  
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus('running');
    setLogs(prevLogs => [...prevLogs, 'Starting LinkedIn Connector Bot...']);
    
    try {
      // In production this would call your backend
      const response = await fetch('http://localhost:5000/run-bot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      if (response.ok) {
        const result = await response.json();
        setLogs(prevLogs => [...prevLogs, `Successfully sent ${result.connectionsSent} connection requests!`]);
        if (result.output) {
          const outputLines = result.output.split('\n').filter(line => line.trim());
          setLogs(prevLogs => [...prevLogs, ...outputLines]);
        }
        setStatus('completed');
      } else {
        const error = await response.json();
        setLogs(prevLogs => [...prevLogs, `Error: ${error.message || 'Unknown error'}`]);
        setStatus('error');
      }
    } catch (error) {
      setLogs(prevLogs => [...prevLogs, `Error: ${error.message || 'Network or server error'}`]);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md overflow-hidden">
        <div className="bg-blue-600 p-6 flex items-center">
          <Linkedin className="text-white mr-3" size={32} />
          <h1 className="text-2xl font-bold text-white">LinkedIn Connection Bot</h1>
        </div>
        
        <div className="p-6">
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="col-span-2 md:col-span-1">
                <label className="block text-gray-700 font-medium mb-2">
                  LinkedIn Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="your.email@example.com"
                  required
                />
              </div>
              
              <div className="col-span-2 md:col-span-1">
                <label className="block text-gray-700 font-medium mb-2">
                  LinkedIn Password
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Your password"
                  required
                />
              </div>
              
              <div className="col-span-2">
                <label className="block text-gray-700 font-medium mb-2">
                  Search Keyword
                </label>
                <input
                  type="text"
                  name="keyword"
                  value={formData.keyword}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. HR Manager, Software Developer, Marketing Manager"
                  required
                />
              </div>
              
              <div className="col-span-1">
                <label className="block text-gray-700 font-medium mb-2">
                  Pages to Search
                </label>
                <input
                  type="number"
                  name="numPages"
                  value={formData.numPages}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="50"
                />
              </div>
              
              <div className="col-span-1">
                <label className="block text-gray-700 font-medium mb-2">
                  Max Connection Requests
                </label>
                <input
                  type="number"
                  name="maxRequests"
                  value={formData.maxRequests}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="80"
                />
              </div>
              
              <div className="col-span-2">
                <label className="block text-gray-700 font-medium mb-2">
                  Connection Message
                </label>
                <textarea
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Add a personalized message (use {name} to include the person's first name)"
                ></textarea>
              </div>
              
              <div className="col-span-2">
                <button
                  type="submit"
                  className={`w-full bg-blue-600 text-white py-3 rounded-md flex items-center justify-center ${loading ? 'opacity-70 cursor-not-allowed' : 'hover:bg-blue-700'}`}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Running Bot...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2" size={18} />
                      Start Sending Connections
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
          
          {status && (
            <div className={`mt-6 p-4 rounded-md ${
              status === 'running' ? 'bg-blue-50 border border-blue-200' :
              status === 'completed' ? 'bg-green-50 border border-green-200' : 
              'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center">
                {status === 'running' && <AlertCircle className="text-blue-500 mr-2" size={20} />}
                {status === 'completed' && <CheckCircle className="text-green-500 mr-2" size={20} />}
                {status === 'error' && <AlertCircle className="text-red-500 mr-2" size={20} />}
                <p className={`font-medium ${
                  status === 'running' ? 'text-blue-700' :
                  status === 'completed' ? 'text-green-700' : 
                  'text-red-700'
                }`}>
                  {status === 'running' ? 'Bot is running...' :
                   status === 'completed' ? 'Bot completed successfully!' : 
                   'An error occurred'}
                </p>
              </div>
            </div>
          )}
          
          {logs.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-700 mb-2">Activity Log</h3>
              <div className="bg-gray-800 text-gray-100 p-4 rounded-md h-64 overflow-y-auto">
                {logs.map((log, index) => (
                  <div key={index} className="mb-1">
                    <span className="text-gray-400">[{new Date().toLocaleTimeString()}]</span> {log}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            Note: This application automates LinkedIn connections. Please use responsibly and in accordance with LinkedIn's terms of service.
          </p>
        </div>
      </div>
    </div>
  );
}

>>>>>>> 572aaa2412c837774f392d15257369281f01a9c3
export default App;