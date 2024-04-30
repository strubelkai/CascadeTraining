
require('dotenv').config() 

const auth_link="https://www.strava.com/oauth/token"

function displayActivities(data){
    const column = Object.keys(data[0]) 
    const head = document.querySelector('thead')
    let tags = "<tr>"
    for (i = 0; i<column.length; i++){
        tags += "<th>"+column[i]+"</th>"
    }
    tags += "</tr>"
    head.innerHTML=tags

    const body = document.querySelector('tbody')
    let rows = ""
    data.map(d => {
        rows+= "<tr><td>" + d.start_date + "</td><td>" + d.name + "</td><td>" + d.sport_type + "</td><td>" + Math.round(d.distance)/1000 + "KM</td</tr>"
    })
    head.innerHTML=rows
}

function getActivities(res){
    
    const activities_link = "https://www.strava.com/api/v3/athlete/activities?access_token="+res.access_token
    fetch(activities_link)
        .then((res) => res.json())
            .then(res => displayActivities(res))
    
}

function reAuthorize(){
    fetch(auth_link,
        {
            method:'post',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json'
            },

            body: JSON.stringify(
                {
                    client_id: process.env.CLIENT_ID,
                    client_secret: process.env.CLIENT_SECRET,
                    refresh_token: process.env.REFRESH_TOKEN,
                    grant_type: 'refresh_token'

                }
            )
        }).then(res => res.json())
            .then(res => getActivities(res))
}



//getActivities()
reAuthorize()