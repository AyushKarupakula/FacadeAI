import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import tensorflow_probability as tfp

class PPOAgent:
    def __init__(self, state_size, action_size, learning_rate=0.0003, gamma=0.99, epsilon=0.2, value_coef=0.5, entropy_coef=0.01):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef

        self.actor = self._build_actor()
        self.critic = self._build_critic()
        self.optimizer = optimizers.Adam(learning_rate)

    def _build_actor(self):
        inputs = layers.Input(shape=(self.state_size,))
        x = layers.Dense(64, activation='relu')(inputs)
        x = layers.Dense(64, activation='relu')(x)
        mean = layers.Dense(self.action_size, activation='tanh')(x)
        std = layers.Dense(self.action_size, activation='softplus')(x)
        return models.Model(inputs, [mean, std])

    def _build_critic(self):
        inputs = layers.Input(shape=(self.state_size,))
        x = layers.Dense(64, activation='relu')(inputs)
        x = layers.Dense(64, activation='relu')(x)
        value = layers.Dense(1)(x)
        return models.Model(inputs, value)

    def get_action(self, state):
        state = np.array(state).reshape(1, -1)
        mean, std = self.actor.predict(state)
        dist = tfp.distributions.Normal(mean, std)
        action = dist.sample()
        return np.clip(action[0], 0, 1)  # Clip action to [0, 1] range

    def train(self, states, actions, rewards, next_states, dones):
        states = np.array(states)
        actions = np.array(actions)
        rewards = np.array(rewards)
        next_states = np.array(next_states)
        dones = np.array(dones)

        # Compute advantages and returns
        values = self.critic.predict(states).flatten()
        next_values = self.critic.predict(next_states).flatten()
        advantages = rewards + self.gamma * next_values * (1 - dones) - values
        returns = advantages + values

        # Normalize advantages
        advantages = (advantages - np.mean(advantages)) / (np.std(advantages) + 1e-8)

        with tf.GradientTape() as tape:
            mean, std = self.actor(states, training=True)
            dist = tfp.distributions.Normal(mean, std)
            new_log_probs = dist.log_prob(actions)
            old_mean, old_std = self.actor.predict(states)
            old_dist = tfp.distributions.Normal(old_mean, old_std)
            old_log_probs = old_dist.log_prob(actions)

            ratio = tf.exp(new_log_probs - old_log_probs)
            clip_ratio = tf.clip_by_value(ratio, 1 - self.epsilon, 1 + self.epsilon)
            policy_loss = -tf.reduce_mean(tf.minimum(ratio * advantages, clip_ratio * advantages))

            value_pred = self.critic(states, training=True)
            value_loss = tf.reduce_mean(tf.square(returns - value_pred))

            entropy = tf.reduce_mean(dist.entropy())

            total_loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy

        grads = tape.gradient(total_loss, self.actor.trainable_variables + self.critic.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.actor.trainable_variables + self.critic.trainable_variables))

        return total_loss.numpy()

    def save(self, actor_path, critic_path):
        self.actor.save_weights(actor_path)
        self.critic.save_weights(critic_path)

    def load(self, actor_path, critic_path):
        self.actor.load_weights(actor_path)
        self.critic.load_weights(critic_path)
