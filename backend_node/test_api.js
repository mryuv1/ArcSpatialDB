const http = require('http');

const testEndpoints = [
    { path: '/api/health', method: 'GET' },
    { path: '/api/projects', method: 'GET' },
    { path: '/api/areas', method: 'GET' }
];

function testAPI() {
    console.log('Testing ArcSpatialDB Node.js API...\n');
    
    testEndpoints.forEach((endpoint, index) => {
        setTimeout(() => {
            const options = {
                hostname: 'localhost',
                port: 5000,
                path: endpoint.path,
                method: endpoint.method
            };

            const req = http.request(options, (res) => {
                let data = '';
                
                res.on('data', (chunk) => {
                    data += chunk;
                });
                
                res.on('end', () => {
                    console.log(`${endpoint.method} ${endpoint.path}`);
                    console.log(`Status: ${res.statusCode}`);
                    
                    try {
                        const json = JSON.parse(data);
                        if (endpoint.path === '/api/health') {
                            console.log(`Response: ${json.message}`);
                        } else if (endpoint.path === '/api/projects') {
                            console.log(`Projects found: ${json.projects ? json.projects.length : 0}`);
                        } else if (endpoint.path === '/api/areas') {
                            console.log(`Areas found: ${json.areas ? json.areas.length : 0}`);
                        }
                    } catch (e) {
                        console.log('Response:', data.substring(0, 100) + '...');
                    }
                    
                    console.log('---\n');
                });
            });

            req.on('error', (e) => {
                console.error(`Error testing ${endpoint.path}:`, e.message);
                console.log('---\n');
            });

            req.end();
        }, index * 1000);
    });
}

// Wait a bit for server to start, then test
setTimeout(testAPI, 2000);
