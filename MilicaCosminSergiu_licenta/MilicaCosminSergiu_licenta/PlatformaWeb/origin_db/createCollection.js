const db = connect("mongodb");

db.createCollection("plan");

db.plan.insertOne({
    "id":"basic",
    "file_size": 1,
    "mode_development": false,
    "mode_offline": false,
    "managment_resource": false
})
db.plan.insertOne({
    "id":"advanced",
    "file_size": 2,
    "mode_development": true,
    "mode_offline": false,
    "managment_resource": false
})

db.plan.insertOne({
    "id":"enterprise",
    "file_size": 1024,
    "mode_development": true,
    "mode_offline": true,
    "managment_resource": true
})

db.origin.createIndex({ owner: 1 })
db.origin.createIndex({ domain: 1 }, { unique: true })
db.plan.createIndex({ id: 1 }, { unique: true })
db.edgeserver.createIndex({ instance_id: 1 }, { unique: true })
db.edgeserver.createIndex({ status: 1 })
