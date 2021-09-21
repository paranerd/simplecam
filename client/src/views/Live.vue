<template>
  <div class="live">
    <h1>Live</h1>

    <div class="col-8 col-s-9">
      <video id="video" autoplay="true" controls="controls"></video>
    </div>
  </div>
</template>

<script>
export default {
  name: "Live",
  created() {
    document.title = `Live | ${process.env.VUE_APP_APP_NAME}`;
  },
  mounted() {
    //this.loadScript('/hls');
    //this.loadScript('http://192.168.178.121:8081/hls');

    const video = document.getElementById("video");
    const videoSrc = "http://192.168.178.121:8081/stream/index.m3u8";

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = videoSrc;
    } else if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(videoSrc);
      hls.attachMedia(video);
    }
  },
  methods: {
    loadScript(url) {
      const scriptElem = document.createElement("script");
      scriptElem.setAttribute("src", url);
      document.head.appendChild(scriptElem);
    },
  },
};
</script>

<style lang="scss" scoped>
.live {
  display: flex;
  justify-items: center;
  align-items: center;
  flex-direction: column;
}

#video {
  width: 100% !important;
  height: auto !important;
}
</style>
