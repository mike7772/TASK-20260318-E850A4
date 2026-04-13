import { createApp } from "vue";
import App from "./App.vue";
import { pinia } from "./app/providers/bootstrap";
import { router } from "./app/router";
import "./styles/theme.css";

createApp(App).use(pinia).use(router).mount("#app");
