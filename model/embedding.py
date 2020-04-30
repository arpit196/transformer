import tensorflow as tf


class EmbeddingSharedWeights(tf.keras.layers.Layer):
    def __init__(self, vocab_size: int, hidden_size: int):
        super(EmbeddingSharedWeights, self).__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size

    def build(self, input_shape: tf.TensorShape) -> None:
        self.shared_weights = self.add_variable(
            name='embedding_shared_weights',
            shape=[self.vocab_size, self.hidden_size],
            dtype=tf.float32,
            initializer=tf.contrib.layers.xavier_initializer()
        )

    def call(self, x: tf.Tensor) -> tf.Tensor:
        mask = tf.to_float(tf.not_equal(x, 0))

        embeddings = tf.gather(self.shared_weights, x)
        embeddings *= tf.expand_dims(mask, -1)
        embeddings *= self.hidden_size ** 0.5

        return embeddings

    def linear(self, x: tf.Tensor) -> tf.Tensor:
        batch_size = tf.shape(x)[0]
        length = tf.shape(x)[1]

        x = tf.reshape(x, [-1, self.hidden_size])
        logits = tf.matmul(x, self.shared_weights, transpose_b=True)

        return tf.reshape(logits, [batch_size, length, self.vocab_size])


class AddLearnedPositionEmbedding(tf.keras.layers.Layer):
    def __init__(self, max_length: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_length = max_length

    def build(self, input_shape: tf.TensorShape) -> None:
        hidden_dim = int(input_shape[-1])
        self.position_embedding = self.add_variable('position_embedding', [self.max_length, hidden_dim])

    def call(self, input: tf.Tensor) -> tf.Tensor:
        batch_size, actual_length, hidden_dim = tf.unstack(tf.shape(input))

        # [batch_size, actual_length, hidden_dim]
        cut_position_embedding = tf.tile(
            tf.expand_dims(self.position_embedding[:actual_length, :], 0),
            [batch_size, 1, 1]
        )

        all_zero = tf.reduce_all(tf.equal(input, 0), axis=-1)  # [batch_size, actual_length]
        mask = tf.tile(tf.expand_dims(all_zero, -1), [1, 1, hidden_dim])  # [batch_size, actual_length, hidden_dim]
        mask_value_tensor = tf.zeros_like(input)  # [batch_size, actual_length, hidden_dim]

        return input + tf.where(mask, mask_value_tensor, cut_position_embedding)
