<?php
header('Content-type:application/json;charset=utf-8');
define('DB_SERVER', 'localhost');
define('DB_USERNAME', 'root');
define('DB_PASSWORD', '');
define('DB_DATABASE', 'emotion_player');

$db = mysqli_connect(DB_SERVER,DB_USERNAME,DB_PASSWORD,DB_DATABASE);

$api_key = 'ENTER_YOUTUBE_API_KEY_HERE'; 
$keyword = ''; 

$khappy = 'happy-music';
$ksad = 'sad-music';
$kangry = 'angry-music';
$ksurprised = 'surprised-music';
$Number = 15;          // Number of searched videos - between 1 and 50
$CNumber = 10;         // Number of searched comments -  between 1 and 50

$maxsum = 1 ; // Initialisation of the maximum score 
$kwords = array( 'it', 'no', 'yes', 'maybe' );   // array of keywords for comment searching

$publishDate = '2018-08-12T00:00:00Z' ;  // Standard format data for searching - excludes videos before the mentioned date

$host = "127.0.0.1";
$port = 25003;
set_time_limit(0);

if (isset($_GET["username"]) && isset($_GET["password"])) {
	$myusername = $_GET["username"];
	$mypassword = $_GET["password"];
}
else {
	echo json_encode(['success' => false, 'message' => 'No username and/or password']);
	exit();
}

if (isset($_GET["emotion"])) {
	$emotion = $_GET["emotion"];
}
else {
	echo json_encode(['success' => false, 'message' => 'No emotion']);
	exit();
}

if ($emotion == 'happy') {
	$keyword = $khappy;
} 

if ($emotion == 'sad') {
	$keyword = $ksad;
}

if ($emotion == 'angry') {
	$keyword = $kangry;
}

if ($emotion == 'surprised') {
	$keyword = $ksurprised;
}


$sql = "SELECT id FROM users WHERE username = '$myusername' and password = '$mypassword'";
$result = mysqli_query($db, $sql);
$row = mysqli_fetch_array($result, MYSQLI_ASSOC);
$count = mysqli_num_rows($result);
      
// If result matched $myusername and $mypassword, table row must be 1 row
if ($count == 1)
{
	$user_id = $row['id'];
	$maxsum = 1; 
	$maxlink = null;
	$songs = [];

	// Main API call based on the parameters 
	$url_data = 'https://www.googleapis.com/youtube/v3/search?part=snippet&q=' . $keyword . '&maxResults=' . $Number .'&publishedAfter=' .  $publishDate . '&key=' . $api_key;
	$data = json_decode(file_get_contents($url_data));    //  Decode the JSON into an associative array after getting the content
	$value = json_decode(json_encode($data), true);       //   Parsing and processing
		
	// Main For function (from 1 to the number of elemets existing in data / value variables)
	for ($i = 0; $i < $Number; $i++) {
		$sum = 1;
		$description = $value['items'][$i]['snippet']['description'];   // Short Description of the video

		if (!array_key_exists('items', $value)) { continue; }
		if (count($value['items']) == 0) { continue; }
		if (!array_key_exists('id', $value['items'][$i])) { continue; }
		if (!array_key_exists('videoId', $value['items'][$i]['id'])) { continue; }

		$videoId = $value['items'][$i]['id']['videoId'];   

		// Getting the first $CNumber of comments from $videoId
		$url_com = 'https://www.googleapis.com/youtube/v3/commentThreads?key=' . $api_key . '&part=snippet&videoId=' . $videoId . '&maxResults=' . $CNumber ;

		// Getting the content, decoding the data into an associative array and parsing the values
		$Cdata = @file_get_contents($url_com);
		$Ctext = json_decode($Cdata, true);

		if ($Ctext == null || !array_key_exists('items', $Ctext)) { continue; }

		foreach ($Ctext['items'] as $val) { 
			$comment = $val['snippet']['topLevelComment']['snippet']['textDisplay']; 
			$lcomment = strtolower($comment);    // Change the text to lowercase for covenience purposes

			foreach ($kwords as &$value2) 
			{
				$sum = $sum + substr_count($lcomment, $value2);
			}

			unset($value2);
		}

		// Since YouTube Data Api V3.01 duration of the video can't be obtained dirrectly anymore. A second api call needs to be done
		// using the same api_key and each video's id. The time format of the durration is ISO8601. In these conditions a data formating is needed. Afterwards the  
		$json_durations = file_get_contents('https://www.googleapis.com/youtube/v3/videos?part=snippet%2CcontentDetails%2Cstatistics%2Cstatus&id='.$videoId.'&key='.$api_key);
		
		$duration = json_decode($json_durations, true);
        foreach ($duration['items'] as $video_time)
       	{
			$video_duration = $video_time['contentDetails']['duration'];
			preg_match('/\d{1,2}[H]/', $video_duration, $hours);
			preg_match('/\d{1,2}[M]/', $video_duration, $minutes);
			preg_match('/\d{1,2}[S]/', $video_duration, $seconds);
			
			$duration = [
				'hours'	  => $hours ? $hours[0] : 0,
				'minutes' => $minutes ? $minutes[0] : 0,
				'seconds' => $seconds ? $seconds[0] : 0,
			];

			$hours = intval(substr($duration['hours'], 0, -1));
			$minutes = intval(substr($duration['minutes'], 0, -1));
			$seconds = intval(substr($duration['seconds'], 0, -1));
			$toltalSeconds = $hours * 3600 + $minutes * 60 + $seconds;
	   	}

		if ($toltalSeconds < 900) {
			$songs[] = [
				'sum' => $sum,
				'videoId' => $videoId,
			];
		}
	}

	usort($songs, function ($song1, $song2) {
		return $song2['sum'] <=> $song1['sum'];
	});

	// print_r($songs);

	foreach ($songs as $song) {
		$id = $song['videoId'];
		$sql = "SELECT * FROM user_history WHERE user_id = '$user_id' and link = '$id'";
		$result = mysqli_query($db, $sql);
		$row = mysqli_fetch_array($result, MYSQLI_ASSOC); 
		$count = mysqli_num_rows($result);

		if ($count == 0) {
			$maxlink = $song['videoId'];
		}
	}

	if ($maxlink == null) {
		$maxlink = $songs[mt_rand(0, count($songs) - 1)];
		$maxlink = $maxlink['videoId'];
	}
	
	$output = "https://www.youtube.com/watch?v=" . $maxlink;
	echo json_encode(['success' => true, 'link' => $output]);

	$sql = "INSERT INTO user_history (user_id, link) VALUES ('$user_id', '$maxlink')";
	if (!mysqli_query($db, $sql)) {
		echo "Error: " . $sql . "<br>" . mysqli_error($db);
	}
} 
else {
	echo json_encode(['success' => true, 'message' => 'Wrong username or password']);
	exit();
}
?>