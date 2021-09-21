<template>
  <div class="recording">
    <h1>{{ this.$route.params.id }}</h1>

    <div class="col-8 col-s-9">
    <video class="video" v-if="src" controls>
      <source :src="src" type="video/mp4">
    </video>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      src: ""
    };
  },
  created() {
    document.title = `Recording | ${process.env.VUE_APP_APP_NAME}`;
  },
  mounted() {
    this.src = process.env.VUE_APP_API_URL + '/records/' + this.$route.params.id;
  },
}
</script>

<style lang="scss" scoped>
.recording {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.video {
  width: 100% !important;
  height: auto !important;
}
</style>
