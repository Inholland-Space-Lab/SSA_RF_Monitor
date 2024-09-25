let previewActive = false

// enable or disable the preview stream
function toggleButton() {
    // get the button so we can change the text appropriately
    const button = document.getElementById('toggleButton')
    if (previewActive){
        // if the preview is already running, stop it:

        // make a request to the server to stop the camera preview
        fetch('/button/stopcam')

        // remove the stream image
        const img = document.getElementById('stream')
        img.remove()

        // change the text of the button
        button.innerHTML = 'Start Preview'
    }else{
        // if the preview is not yet running, start it:

        // make a request to the server to start the camera preview
        fetch('/button/startcam').then(()=>{
            // after the camera started, create the stream image
            const img = document.createElement('img')
            img.setAttribute('id', 'stream')
            img.setAttribute('src', 'stream.mjpg')
            img.setAttribute('width', '640')
            img.setAttribute('height', '480')
            img.setAttribute('alt', 'Camera Offline')

            // add the image to the div element in the webpage
            const div = document.getElementById('streamdiv')
            div.appendChild(img)
        })

        // change the text of the button
        button.innerHTML = 'Stop Preview'
    }
    // toggle the state of the preview variable
    previewActive = !previewActive
}

function startBelt() {
    // make a request to the server to start the belt
    fetch('/button/startbelt')
}
function stopBelt() {
    // make a request to the server to stop the belt
    fetch('/button/stopbelt')
}

function pictureButton() {
    // make a request to the server to take a picture, and open it
    // TODO: request the url/name of the taken picture and redirect to that
    redirect('/button/picture')
}

function browseButton() {
    redirect('/pictures')
}

// Deprecated
function redirect(url){
    // add the current protocol, site name and port to the url
    // this allows this function to change to a different page on the same site
    const newPage = 'http://' + window.location.host + url
    // since the host/site name is the ip address of the raspberry,
    // and thus will change depending on what network it is connected to, I did not want to hardcode the address in

    // log the page we are redirecting to
    console.debug("redirecting to:", newPage)

    // change the url of the browser to the new page
    open(newPage)
    // window.location.href = newPage
}
