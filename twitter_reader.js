const AWS = require("aws-sdk");
const Twitter = require("twitter-lite");

// env
const twitterUserName = "ysano";
const region = "ap-northeast-1";
const deliveryStreamName = "Twitter-Dashboard-Raw";
const secretName = "TwitterAPI-Secrets";
// env end

const firehose = new AWS.Firehose({apiVersion: '2015-08-04', region: region });
const secretsManager = new AWS.SecretsManager({ region: region });

async function getSecrets(){
    const data = await secretsManager.getSecretValue({SecretId: secretName}).promise();
    return JSON.parse(data.SecretString);
}

async function putRecordToFirehose(tweet){
    const recordParams = {
        DeliveryStreamName: deliveryStreamName,
        Record: {
            Data: JSON.stringify(tweet) + '\n'
        }
    }
    //console.log("putRecordToFirehose: " + JSON.stringify(tweet));
    await firehose.putRecord(recordParams).promise();
}

async function main(){
    try{
        const secrets = await getSecrets();
        const twitter = new Twitter({
            consumer_key: secrets.ConsumerApiKey,
            consumer_secret: secrets.ConsumerApiSecret,
            access_token_key: secrets.AccessToken,
            access_token_secret: secrets.AccessTokenSecret
        });
        
        // follower取得
        const followIds = await twitter.get("friends/ids", {screen_name: twitterUserName, count: 5000});
        //console.log(followIds);
        
        // tweet断続取得
        twitter.stream("statuses/filter", { follow: followIds.ids.join(",")})
        .on("start", _ => console.log("start"))
        .on("data", putRecordToFirehose)
        .on("error", error => console.log("error", error))
        .on("end", _ => console.log("end"));
    } catch (e) {
        console.log(e);
    }
}
main();
