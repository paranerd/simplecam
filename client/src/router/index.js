import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Live from "../views/Live.vue";
import Archive from "../views/Archive.vue";
import Recording from "../views/Recording.vue";

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
  },
  {
    path: "/live",
    name: "Live",
    component: Live,
  },
  {
    path: "/archive",
    name: "Archive",
    component: Archive,
  },
  {
    path: "/recording/:id",
    name: "Recording",
    component: Recording,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
