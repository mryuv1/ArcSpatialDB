const http = require('http');

function testFiltering() {
    console.log('Testing filtering with a real HTTP request...\n');
    
    // First, test without filters
    console.log('1. Testing without filters:');
    const req1 = http.request({
        hostname: 'localhost',
        port: 5000,
        path: '/api/projects?page=1&per_page=3',
        method: 'GET'
    }, (res1) => {
        let data1 = '';
        res1.on('data', chunk => data1 += chunk);
        res1.on('end', () => {
            try {
                const json1 = JSON.parse(data1);
                console.log(`   Found ${json1.projects.length} projects total`);
                json1.projects.forEach(p => console.log(`   - ${p.uuid}: ${p.project_name}`));
                
                // Now test with UUID filter using first project's UUID prefix
                const testUuid = json1.projects[0].uuid.substring(0, 4);
                console.log(`\n2. Testing with UUID filter "${testUuid}":`);
                
                const req2 = http.request({
                    hostname: 'localhost',
                    port: 5000,
                    path: `/api/projects?page=1&per_page=10&uuid_filter=${testUuid}`,
                    method: 'GET'
                }, (res2) => {
                    let data2 = '';
                    res2.on('data', chunk => data2 += chunk);
                    res2.on('end', () => {
                        try {
                            const json2 = JSON.parse(data2);
                            console.log(`   Found ${json2.projects.length} filtered projects`);
                            json2.projects.forEach(p => console.log(`   - ${p.uuid}: ${p.project_name}`));
                            
                            if (json2.projects.length < json1.projects.length) {
                                console.log('\n✅ Filtering is WORKING correctly!');
                            } else {
                                console.log('\n❌ Filtering is NOT working - same number of results');
                            }
                            
                        } catch (e) {
                            console.log('   Error parsing filtered response:', e.message);
                        }
                        process.exit(0);
                    });
                });
                
                req2.on('error', (e) => {
                    console.log('   Error in filtered request:', e.message);
                    process.exit(1);
                });
                
                req2.end();
                
            } catch (e) {
                console.log('   Error parsing response:', e.message);
                process.exit(1);
            }
        });
    });
    
    req1.on('error', (e) => {
        console.log('Error in request:', e.message);
        process.exit(1);
    });
    
    req1.end();
}

testFiltering();
